"""Module for handling client connections and messages in the server."""

from protocol import recv_json_line, send_json
devices = {}
units = {}


def handle_client(sock, addr):
    """Handle incoming client messages."""
    while True:
        msg = recv_json_line(sock)
        if msg is None:
            print(f"Connection closed by {addr}")
            break
        handle_message(sock, msg)


def handle_message(sock, msg):
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
            "type": "device_state_update",
            "sender_id": "server",
            "payload": {
                "deviceId": device_id,
                "state": payload
            }
        })


def handle_get_devices(sockt):
    """Send a list of registered devices to the client."""
    device_list = [
        {"deviceId": dev_id, "deviceType": device["type"]}
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
    """Send the UI definition for a specified device to the client."""
    device_id = payload["deviceId"]
    send_json(sock, {
        "type": "ui_definition",
        "sender_id": "server",
        "payload": {
            "deviceId": device_id,
            "ui": devices[device_id]["ui"]
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
    units[unit_id] = sock