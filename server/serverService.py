
"""Module for handling client connections and messages in the server."""

# =========================================================
# IMPORTS
# =========================================================
from protocol import recv_json_line, send_json
from db_service import *

from src.rbac import (
    Permission,
    enforce_permission,
    filter_devices_for_user,
    normalize_role,
    user_can_access_device,
)
from src.scenes import (
    SceneNotFoundError,
    create_scene,
    get_scene,
    set_dispatcher,
    trigger_scene,
)
from src.speech_to_text import process_voice_command, register_device_alias

# =========================================================
# GLOBAL SERVER STATE (In-Memory)
# =========================================================
devices = {}
units = {}
unit_sockets = {}
# socket -> {userId, email, role} (Iteration 4/5 session cache)
authenticated_users = {}

# Added validation for allowed message types & required payload fields
ALLOWED_MESSAGE_TYPES = {
    "register_device",
    "ui_definition",
    "device_state",
    "get_devices",
    "get_ui",
    "action",
    "login",
    "trigger_scene",
    "voice_command",
}

REQUIRED_PAYLOAD_FIELDS = {
    "register_device": ["deviceType"],
    "ui_definition": ["ui"],
    "device_state": ["state"],
    "get_devices": [],
    "get_ui": ["deviceId"],
    "action": ["deviceId", "action"],
    "login": ["email", "password"],
    "trigger_scene": ["sceneId"],
    "voice_command": ["text"],
}


# =========================================================
# CLIENT CONNECTION HANDLING
# =========================================================
def handle_client(sock, addr):
    buffered = sock.makefile("r", encoding="utf-8", newline="\n")
    client_id = None

    try:
        while True:
            try:
                msg = recv_json_line(buffered)
                if msg is None:
                    log_event("CONNECTION_CLOSED", str(addr))
                    break

                if not validate_base_message(sock, msg):
                    log_event("INVALID_MESSAGE", str(msg))
                    continue

                client_id = handle_message(sock, msg, client_id)

            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"Client {addr} disconnected ({e})")
                break

    finally:
        authenticated_users.pop(sock, None)
        if sock in unit_sockets:
            uid = unit_sockets.pop(sock)
            if uid in units:
                units[uid].discard(sock)
                if not units[uid]:
                    units.pop(uid)

        if client_id and client_id in devices:
            print(f"Removing device {client_id}")
            devices.pop(client_id, None)

        try:
            buffered.close()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass


# For Cleaner logs, easier testing/demo.
def log_event(event, details=""):
    """Simple server log helper."""
    print(f"[SERVER] {event} | {details}")


# If a unit/device socket dies while server sends data, your server should not crash.
def safe_send_json(sock, msg):
    """Safely send JSON without crashing the server."""
    try:
        send_json(sock, msg)
        return True
    except (BrokenPipeError, ConnectionResetError, OSError, AttributeError) as e:
        log_event("SEND_FAILED", str(e))
        return False


def send_error(sock, message):
    """Send error response using existing non-breaking protocol."""
    safe_send_json(sock, {
        "type": "error",
        "sender_id": "server",
        "payload": {"message": message}
    })


# =========================================================
# For Validation
# =========================================================

def validate_base_message(sock, msg):
    """Validate the basic structure of an incoming message."""
    print("VALIDATING TYPE:", msg.get("type"))  # Just for debugging
    if not isinstance(msg, dict):
        send_error(sock, "Message must be a JSON object")
        return False

    if "type" not in msg:
        send_error(sock, "Missing field: type")
        return False

    if "sender_id" not in msg:
        send_error(sock, "Missing field: sender_id")
        return False

    if "payload" not in msg:
        send_error(sock, "Missing field: payload")
        return False

    if not isinstance(msg["payload"], dict):
        send_error(sock, "Payload must be an object")
        return False

    if msg["type"] not in ALLOWED_MESSAGE_TYPES:
        print("❌ INVALID TYPE:", msg["type"])
        send_error(sock, f"Unknown message type: {msg['type']}")
        return False

    return True

def validate_payload_fields(sock, msg_type, payload):
    """Validate required payload fields for a given message type."""
    required_fields = REQUIRED_PAYLOAD_FIELDS.get(msg_type, [])

    for field in required_fields:
        if field not in payload:
            print(f"❌ MISSING FIELD: {field} in {msg_type}")
            send_error(sock, f"Missing payload field: {field}")
            return False

    return True
# =========================================================
# MESSAGE ROUTER
# =========================================================

def handle_message(sock, msg, client_id):
    """Handle incoming messages from clients."""
    msg_type = msg["type"]
    sender_id = msg["sender_id"]
    payload = msg["payload"]

    if not validate_payload_fields(sock, msg_type, payload):
        log_event("INVALID_PAYLOAD", f"type={msg_type}, payload={payload}")
        return client_id

    if msg_type == "register_device":
        handle_register_device(sock, sender_id, payload)
    elif msg_type == "ui_definition":
        handle_ui_definition(sender_id, payload)
    elif msg_type == "device_state":
        handle_device_state(sender_id, payload)
    elif msg_type == "get_devices":
        handle_get_devices(sock)
    elif msg_type == "get_ui":
        handle_get_ui(sock, sender_id, payload)
    elif msg_type == "action":
        handle_action(sock, sender_id, payload)
    elif msg_type == "login":
        handle_login_for_gui(sock, sender_id, payload)
    elif msg_type == "trigger_scene":
        handle_trigger_scene(sock, sender_id, payload)
    elif msg_type == "voice_command":
        handle_voice_command_message(sock, sender_id, payload)
    else:
        send_error(sock, f"Unsupported message type: {msg_type}")
        return client_id
    return sender_id or client_id


# =========================================================
# DEVICE HANDLERS
# =========================================================

def handle_register_device(sock, sender_id, payload):
    """Register a new device with the given socket and information."""
    devices[sender_id] = {
        "socket": sock,
        "info": payload,
        "ui": None,
        "state": None
    }

    device_type = payload.get("deviceType", "unknown")
    upsert_device(sender_id, device_type)

    print(f"Registered device {sender_id} with info {payload}")


def handle_ui_definition(sender_id, payload):
    """Handle the UI definition from a registered device."""
    if sender_id in devices:
        ui = payload["ui"]
        devices[sender_id]["ui"] = ui

        save_ui_defination(sender_id, ui)

        print(f"Received UI definition from {sender_id}: {payload}")
    else:
        print(f"UI definition from unregistered device {sender_id}")


def _device_type_for(device_id: str):
    d = devices.get(device_id)
    if d:
        return d.get("info", {}).get("deviceType")
    return fetch_device_type(device_id)


def _state_dict_to_action(state):
    if isinstance(state, str):
        return state
    if not isinstance(state, dict):
        return None
    if "action" in state:
        return state["action"]
    if "lightOn" in state:
        return "on" if state.get("lightOn") else "off"
    p = state.get("power")
    if isinstance(p, str):
        return p.lower()
    return None


def _forward_device_action(device_id, action, sender_id):
    if device_id not in devices:
        log_event("ACTION_SKIP_OFFLINE", str(device_id))
        return
    safe_send_json(devices[device_id]["socket"], {
        "type": "action",
        "sender_id": sender_id,
        "payload": {
            "action": action
        }
    })


def _scene_state_dispatch(device_id, state):
    action = _state_dict_to_action(state)
    if action is None:
        log_event("SCENE_DISPATCH_SKIP", f"{device_id} state={state!r}")
        return
    _forward_device_action(device_id, action, "server")


# Device ➜ Server ➜ Units
def handle_device_state(device_id, payload):
    """Update the state of a device and notify all units of the change."""
    state = payload["state"]

    if device_id not in devices:
        print(f"State from unregistered device {device_id}: {state}")
        return

    devices[device_id]["state"] = state

    save_device_state(device_id, state)

    for user_sockets in list(units.values()):
        for unit_sock in list(user_sockets):
            safe_send_json(unit_sock, {
                "type": "state_update",
                "sender_id": "server",
                "payload": {
                    "deviceId": device_id,
                    "state": state
                }
            })

    run_automation_from_device_state(device_id, state)


def run_automation_from_device_state(device_id, state):
    """Server-side rules when sensors push state (Iteration 4/5)."""
    if not isinstance(state, dict):
        return
    if state.get("motionDetected") is True:
        for lid in ("led-1", "led-2"):
            if lid in devices:
                _forward_device_action(lid, "on", "automation")
    if state.get("motionDetected") is False:
        for lid in ("led-1", "led-2"):
            if lid in devices:
                _forward_device_action(lid, "off", "automation")
    if state.get("smokeDetected") is True and "alarm-1" in devices:
        _forward_device_action("alarm-1", "on", "automation")
    t = state.get("temperature")
    if isinstance(t, (int, float)) and t > 28.0 and "fan-1" in devices:
        _forward_device_action("fan-1", "on", "automation")


def handle_get_devices(sockt):
    """Send a list of registered devices to the client."""
    if not require_login(sockt):
        return
    user_id = unit_sockets.get(sockt)
    raw = fetch_devices_list()
    device_list = filter_devices_for_user(str(user_id), raw)
    send_json(sockt, {
        "type": "device_list",
        "sender_id": "server",
        "payload": {
            "devices": device_list
        }
    })


# Server ➜ Unit
def handle_get_ui(sock, unit_id, payload):
    if not require_login(sock):
        return
    user_id = unit_sockets.get(sock)
    device_id = payload["deviceId"]
    dtype = _device_type_for(device_id)
    if not user_can_access_device(
        str(user_id), device_id, device_type=dtype, need_control=False
    ):
        send_error(sock, "Access denied for this device")
        return

    device = devices.get(device_id)

    if not device:
        result = fetch_device_ui_and_state(device_id)
        if result is None:
            send_error(sock, f"Unknown deviceId {device_id}")
            return

        ui, state = result
        safe_send_json(sock, {
            "type": "ui_definition",
            "sender_id": "server",
            "payload": {"deviceId": device_id, "ui": ui, "state": state}
        })
        return

    safe_send_json(sock, {
        "type": "ui_definition",
        "sender_id": "server",
        "payload": {
            "deviceId": device_id,
            "ui": device.get("ui") or [],
            "state": device.get("state") or {}
        }
    })


# Unit ➜ Server ➜ Device
def handle_action(sock, unit_id, payload):
    """Forward a unit action to a device after login and device-type RBAC."""
    if not require_login(sock):
        return

    user_id = unit_sockets.get(sock)
    device_id = payload["deviceId"]
    action = payload["action"]
    dtype = _device_type_for(device_id)
    if not user_can_access_device(
        str(user_id), device_id, device_type=dtype, need_control=True
    ):
        send_error(sock, "Access denied for this device")
        return

    if device_id in devices:
        _forward_device_action(device_id, action, unit_id)
    else:
        send_error(sock, f"Device {device_id} is not connected")
    return


def _execute_trigger_scene(sock, user_id, scene_id):
    scene = get_scene(scene_id)
    if scene is None:
        send_error(sock, f"Unknown scene: {scene_id}")
        return
    device_states = scene.get("device_states") or {}
    for dev_id in device_states:
        dtype = _device_type_for(str(dev_id))
        if not user_can_access_device(
            str(user_id), str(dev_id), device_type=dtype, need_control=True
        ):
            send_error(
                sock,
                f"Access denied for device {dev_id} in this scene",
            )
            return
    try:
        trigger_scene(scene_id)
    except SceneNotFoundError:
        send_error(sock, f"Unknown scene: {scene_id}")
        return
    safe_send_json(sock, {
        "type": "scene_triggered",
        "sender_id": "server",
        "payload": {
            "sceneId": scene_id,
            "message": "Scene applied",
        },
    })


def handle_trigger_scene(sock, unit_id, payload):
    if not require_login(sock):
        return
    user_id = unit_sockets.get(sock)
    if not user_id or not enforce_permission(
        sock, str(user_id), Permission.SCENE_TRIGGER, send_error
    ):
        return
    scene_id = payload.get("sceneId")
    if not scene_id:
        send_error(sock, "Missing sceneId")
        return
    _execute_trigger_scene(sock, str(user_id), str(scene_id))


def handle_voice_command_message(sock, unit_id, payload):
    if not require_login(sock):
        return
    user_id = unit_sockets.get(sock)
    text = payload.get("text")
    intent = process_voice_command(text)
    itype = intent.get("type")
    if itype == "scene":
        if not enforce_permission(
            sock, str(user_id), Permission.SCENE_TRIGGER, send_error
        ):
            return
        scene_id = intent.get("sceneId") or intent.get("scene")
        if not scene_id:
            send_error(sock, "Could not resolve scene from voice")
            return
        _execute_trigger_scene(sock, str(user_id), str(scene_id))
        return
    if itype == "action":
        if not enforce_permission(
            sock, str(user_id), Permission.DEVICE_CONTROL, send_error
        ):
            return
        device_id = intent.get("deviceId")
        action = intent.get("action")
        if not device_id or not action:
            send_error(sock, "Could not parse device action from voice")
            return
        dtype = _device_type_for(str(device_id))
        if not user_can_access_device(
            str(user_id), str(device_id), device_type=dtype, need_control=True
        ):
            send_error(sock, "Access denied for this device")
            return
        if device_id in devices:
            _forward_device_action(device_id, action, unit_id)
            safe_send_json(sock, {
                "type": "voice_command_ok",
                "sender_id": "server",
                "payload": {"message": intent.get("message", "ok")},
            })
        else:
            send_error(sock, f"Device {device_id} is not connected")
        return
    send_error(sock, intent.get("message", "Could not understand command"))


# =========================================================
# AUTH HELPERS
# =========================================================

def handle_login(sock, unit_id, payload):
    """Handle the login request from a unit and associate it with a socket."""
    units.setdefault(unit_id, set()).add(sock)
    unit_sockets[sock] = unit_id


def is_logged_in(sock):
    """To check if user is logged in, returns True or False
    based on store unit socket in units dict using userId as key"""
    return sock in unit_sockets


def require_login(sock):
    """
    Check login. If not logged in, send error and return False.
    If logged in, return True.
    """
    if not is_logged_in(sock):
        send_error(sock, "Please login first")
        return False
    return True


def handle_login_for_gui(sock, unit_id, payload):

    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        safe_send_json(sock, {
            "type": "login_failed",
            "sender_id": "server",
            "payload": {"message": "Missing email or password"}
        })
        return

    ok, user = verify_login(email, password)

    if not ok:
        safe_send_json(sock, {
            "type": "login_failed",
            "sender_id": "server",
            "payload": {"message": "Invalid email or password"}
        })
        return

    user_id = str(user["userId"])
    units.setdefault(user_id, set()).add(sock)
    unit_sockets[sock] = user_id
    role = normalize_role(user.get("role"))
    authenticated_users[sock] = {
        "userId": user["userId"],
        "email": user.get("email"),
        "role": role,
    }

    safe_send_json(sock, {
        "type": "login_ok",
        "sender_id": "server",
        "payload": {
            "userId": user["userId"],
            "role": role,
            "message": "Login successful"
        }
    })


def _ensure_default_scenes():
    """Seed good_morning / good_night if scenes.json is empty."""
    morning = {
        "led-1": {"action": "on"},
        "led-2": {"action": "on"},
        "door-1": {"action": "open"},
        "fan-1": {"action": "on"},
    }
    night = {
        "led-1": {"action": "off"},
        "led-2": {"action": "off"},
        "door-1": {"action": "close"},
        "fan-1": {"action": "off"},
    }
    for name, states in (("good_morning", morning), ("good_night", night)):
        if get_scene(name) is None:
            try:
                create_scene(name, states)
            except Exception as exc:
                log_event("SCENE_SEED_FAIL", f"{name}: {exc}")


def _register_speech_device_aliases():
    pairs = [
        ("led", "led-1"),
        ("led one", "led-1"),
        ("led 1", "led-1"),
        ("light", "led-1"),
        ("lights", "led-1"),
        ("fan", "fan-1"),
        ("door", "door-1"),
    ]
    for spoken, canonical in pairs:
        try:
            register_device_alias(spoken, canonical)
        except Exception as exc:
            log_event("SPEECH_ALIAS_FAIL", f"{spoken}: {exc}")


_ensure_default_scenes()
_register_speech_device_aliases()
set_dispatcher(_scene_state_dispatch)
