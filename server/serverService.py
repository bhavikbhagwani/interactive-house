
"""Module for handling client connections and messages in the server."""

# =========================================================
# IMPORTS
# =========================================================
from protocol import recv_json_line, send_json
from db_service import *

# =========================================================
# GLOBAL SERVER STATE (In-Memory)
# =========================================================
devices = {}
units = {}
unit_sockets = {}

# Added validation for allowed message types & required payload fields
ALLOWED_MESSAGE_TYPES = {
    "register_device",
    "ui_definition",
    "device_state",
    "get_devices",
    "get_ui",
    "action",
    "login",
}

REQUIRED_PAYLOAD_FIELDS = {
    "register_device": ["deviceType"],
    "ui_definition": ["ui"],
    "device_state": ["state"],
    "get_devices": [],
    "get_ui": ["deviceId"],
    "action": ["deviceId", "action"],
    "login": ["email", "password"],
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
                # new add
                msg = recv_json_line(buffered)
                if msg is None:
                    log_event("CONNECTION_CLOSED", str(addr))
                    break

                if not validate_base_message(sock, msg):
                    log_event("INVALID_MESSAGE", str(msg))
                    continue

                client_id = handle_message(sock, msg, client_id) #handle msg func. call
# new add end
# ------------
                # msg = recv_json_line(buffered)
                # if msg is None:
                #     print(f"Connection closed by {addr}")
                #     break
                # client_id = handle_message(sock, msg, client_id)  #handle msg func. call

            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"Client {addr} disconnected ({e})")
                break

    finally:
        # Remove unit by socket mapping (works even if client_id != user_id)
        if sock in unit_sockets:
            uid = unit_sockets.pop(sock)
            print(f"Removing unit {uid}")
            units.pop(uid, None)

        # Keep your device cleanup as-is
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
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
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

# To stop malformed messages from crashing the server.
def validate_base_message(sock, msg):
    """Validate the basic structure of an incoming message."""
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
        send_error(sock, f"Unknown message type: {msg['type']}")
        return False

    return True

def validate_payload_fields(sock, msg_type, payload):
    """Validate required payload fields for a given message type."""
    required_fields = REQUIRED_PAYLOAD_FIELDS.get(msg_type, [])

    for field in required_fields:
        if field not in payload:
            send_error(sock, f"Missing payload field: {field}")
            return False

    return True
# =========================================================
# MESSAGE ROUTER
# =========================================================

def handle_message(sock, msg, client_id):
    """Handle incoming messages from clients."""
    # msg_type = msg["type"]
    # sender_id = msg["sender_id"]
    # payload = msg["payload"]
    # print("LOGIN PAYLOAD:", payload)
    #  new add 
    msg_type = msg["type"]
    sender_id = msg["sender_id"]
    payload = msg["payload"]

    if not validate_payload_fields(sock, msg_type, payload):
        log_event("INVALID_PAYLOAD", f"type={msg_type}, payload={payload}")
        return client_id
    #  new add end
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
    # new add
    else: #Extra fallback
        send_error(sock, f"Unsupported message type: {msg_type}")
        return client_id
    #  new add in
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

    #DB : insert/update device
    device_type = payload.get("deviceType", "unknown")  #unknown used to present python program crash
    upsert_device(sender_id, device_type)
    
    print(f"Registered device {sender_id} with info {payload}")



def handle_ui_definition(sender_id, payload):
    """Handle the UI definition from a registered device."""
    if sender_id in devices:
        ui = payload["ui"]
        devices[sender_id]["ui"] = ui

        # DB save uiDefinition in DB
        save_ui_defination(sender_id, ui)

        print(f"Received UI definition from {sender_id}: {payload}")
    else:
        print(f"UI definition from unregistered device {sender_id}")


# Device ➜ Server ➜ Units
def handle_device_state(device_id, payload):
    """Update the state of a device and notify all units of the change."""
    state = payload["state"]

    if device_id not in devices:
        print(f"State from unregistered device {device_id}: {state}")
        return
    
    devices[device_id]["state"] = state

    # DB Save device state in DB
    save_device_state(device_id, state)

    # notify units - If one unit socket is dead, server should survive.
    # Using list(units.values()) is safer while iterating.
    # new add
    for unit_sock in list(units.values()):
        safe_send_json(unit_sock, {
            "type": "state_update",
            "sender_id": "server",
            "payload": {
                "deviceId": device_id,
                "state": state
            }
        })
        #  new add end
    # # notify units
    # for unit_sock in units.values():
    #     send_json(unit_sock, {
    #         "type": "state_update",
    #         "sender_id": "server",
    #         "payload": {
    #             "deviceId": device_id,
    #             "state": state
    #         }
    #     })


def handle_get_devices(sockt):
    """Send a list of registered devices to the client."""
    if not require_login(sockt):
        return
    device_list = fetch_devices_list()
    send_json(sockt, {
        "type": "device_list",
        "sender_id": "server",
        "payload": {
            "devices": device_list
        }
    })


# Server ➜ Unit
# Sends UI + current state so unit can draw controls.
# Unit asks for device UI
#         ↓
# Is device online?
#         ↓
#    YES → Send from memory
#    NO  → Check database
#             ↓
#         Found? → Send from DB
#         Not found? → Send error
def handle_get_ui(sock, unit_id, payload):
    if not require_login(sock):
        return
    device_id = payload["deviceId"]
    device = devices.get(device_id)

    if not device:
        # fallback to DB (device might be offline but still stored)
        result = fetch_device_ui_and_state(device_id)
        if result is None:
            # safe_send_json(sock, {
            #     "type": "error",
            #     "sender_id": "server",
            #     "payload": {"message": f"Unknown deviceId {device_id}"}
            # })
            # new add 1 line
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
    """Handle an action request from a unit for a specific device based on login status."""
    if not require_login(sock):
        return
    
    device_id = payload["deviceId"]
    action = payload["action"]
    if device_id in devices:
        safe_send_json(devices[device_id]["socket"], {
            "type": "action",
            "sender_id": unit_id,
            "payload": {
                "action": action
            }
        })
    else:
        # send_json(sock, {
        #     "type": "error",
        #     "sender_id": "server",
        #     "payload": {"message": f"Device {device_id} is not connected"}
        # })
        send_error(sock, f"Device {device_id} is not connected")
    return



# =========================================================
# AUTH HELPERS
# =========================================================

def handle_login(sock, unit_id, payload):
    """Handle the login request from a unit and associate it with a socket."""
    units[unit_id] = sock


def is_logged_in(sock):
    """To check if user is logged in, returns True or False 
    based on store unit socket in units dict using userId as key"""
    return sock in units.values()


def require_login(sock):
    """
    Check login. If not logged in, send error and return False.
    If logged in, return True.
    """
    if not is_logged_in(sock):
        send_error(sock, "Please login first")
        # send_json(sock, {
        #     "type": "error",
        #     "sender_id": "server",
        #     "payload": {"message": "Please login first"}
        # })
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
    units[user_id] = sock
    unit_sockets[sock] = user_id

    safe_send_json(sock, {
        "type": "login_ok",
        "sender_id": "server",
        "payload": {
            "userId": user["userId"],
            "role": user["role"],
            "message": "Login successful"
        }
    })
