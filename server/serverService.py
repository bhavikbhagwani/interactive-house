"""Module for handling client connections and messages in the server."""
from protocol import recv_json_line, send_json
devices = {}
units = {}


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
                client_id = handle_message(sock, msg, client_id)

            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"Client {addr} disconnected ({e})")
                break

    finally:
        if client_id:
            if client_id in units:
                print(f"Removing unit {client_id}")
                units.pop(client_id, None)
            if client_id in devices:
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



def handle_message(sock, msg, client_id):
    """Handle incoming messages from clients."""
    msg_type = msg["type"]
    sender_id = msg["sender_id"]
    payload = msg["payload"]
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
        handle_action(sender_id, payload)
    elif msg_type == "login":
        handle_login(sock, sender_id, payload)

    return sender_id or client_id


def handle_register_device(sock, sender_id, payload):
    """Register a new device with the given socket and information."""
    devices[sender_id] = {
        "socket": sock,
        "info": payload,
        "ui": None,
        "state": None
    }
    print(f"Registered device {sender_id} with info {payload}")


def handle_ui_definition(sender_id, payload):
    """Handle the UI definition from a registered device."""
    if sender_id in devices:
        devices[sender_id]["ui"] = payload["ui"]
        print(f"Received UI definition from {sender_id}: {payload}")
    else:
        print(f"UI definition from unregistered device {sender_id}")


def handle_device_state(device_id, payload):
    """Update the state of a device and notify all units of the change."""
    devices[device_id]["state"] = payload["state"]
    for unit_sock in units.values():
        send_json(unit_sock, {
            "type": "state_update",
            "sender_id": "server",
            "payload": {
                "deviceId": device_id,
                "state": payload["state"]
            }
        })


def handle_get_devices(sockt):
    """Send a list of registered devices to the client."""
    device_list = [
        {"deviceId": dev_id, "deviceType": device["info"].get("deviceType")}
        for dev_id, device in devices.items()
    ]
    send_json(sockt, {
        "type": "device_list",
        "sender_id": "server",
        "payload": {
            "devices": device_list
        }
    })


def handle_get_ui(sock, unit_id, payload):
    device_id = payload["deviceId"]
    device = devices.get(device_id)

    if not device:
        send_json(sock, {
            "type": "error",
            "sender_id": "server",
            "payload": {"message": f"Unknown deviceId {device_id}"}
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


def handle_action(unit_id, payload):
    """Handle an action request from a unit for a specific device."""
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


def handle_login(sock, unit_id, payload):
    """Handle the login request from a unit and associate it with a socket."""
    username = payload.get("username")
    password = payload.get("password")

    # SIMPLE CREDENTIAL CHECK
    if username == "user" and password == "1234":
        units[unit_id] = sock

        send_json(sock, {
            "type": "login_ok",
            "sender_id": "server",
            "payload": {"success": True}
        })

        print(f"Login SUCCESS for {unit_id} (username={username})")

    else:
        send_json(sock, {
            "type": "error",
            "sender_id": "server",
            "payload": {"message": "login_failed"}
        })

        print(f"Login FAILED for {unit_id} (username={username})")