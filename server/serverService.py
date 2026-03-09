
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
                    print(f"Connection closed by {addr}")
                    break
                client_id = handle_message(sock, msg, client_id)  #handle msg func. call

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


# =========================================================
# MESSAGE ROUTER
# =========================================================

def handle_message(sock, msg, client_id):
    """Handle incoming messages from clients."""
    msg_type = msg["type"]
    sender_id = msg["sender_id"]
    payload = msg["payload"]
    print("LOGIN PAYLOAD:", payload)
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

    # notify units
    for unit_sock in units.values():
        send_json(unit_sock, {
            "type": "state_update",
            "sender_id": "server",
            "payload": {
                "deviceId": device_id,
                "state": state
            }
        })


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
            send_json(sock, {
                "type": "error",
                "sender_id": "server",
                "payload": {"message": f"Unknown deviceId {device_id}"}
            })
            return

        ui, state = result
        send_json(sock, {
            "type": "ui_definition",
            "sender_id": "server",
            "payload": {"deviceId": device_id, "ui": ui, "state": state}
        })
        return
    
    send_json(sock, {
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
        send_json(devices[device_id]["socket"], {
            "type": "action",
            "sender_id": unit_id,
            "payload": {
                "action": action
            }
        })
    else:
        send_json(sock, {
            "type": "error",
            "sender_id": "server",
            "payload": {"message": f"Device {device_id} is not connected"}
        })
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
        send_json(sock, {
            "type": "error",
            "sender_id": "server",
            "payload": {"message": "Please login first"}
        })
        return False
    return True


def handle_login_for_gui(sock, unit_id, payload):

    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        send_json(sock, {
            "type": "login_failed",
            "sender_id": "server",
            "payload": {"message": "Missing email or password"}
        })
        return

    ok, user = verify_login(email, password)

    if not ok:
        send_json(sock, {
            "type": "login_failed",
            "sender_id": "server",
            "payload": {"message": "Invalid email or password"}
        })
        return

    user_id = str(user["userId"])
    units[user_id] = sock
    unit_sockets[sock] = user_id

    send_json(sock, {
        "type": "login_ok",
        "sender_id": "server",
        "payload": {
            "userId": user["userId"],
            "role": user["role"],
            "message": "Login successful"
        }
    })