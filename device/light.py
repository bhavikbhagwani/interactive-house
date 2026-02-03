import socket
from protocol import send_json, recv_json_line

SERVER_HOST = "localhost"
SERVER_PORT = 5001

# Unique identifier for this device
DEVICE_ID = "light-1"


def send_register_device(sock):
    """
    Inform the server that this client is a device.
    This message is sent once when the device connects.
    """
    msg = {
        "type": "register_device",
        "sender_id": DEVICE_ID,          
        "payload": {
            "deviceType": "light"
        }
    }
    print("SEND: register_device", msg)
    send_json(sock, msg)


def send_ui_definition(sock):
    """
    Send the UI definition to the server.
    The device defines which controls it supports (ON / OFF buttons).
    The unit will later render this UI.
    """
    ui = [
        {"type": "button", "action": "ON", "label": "Turn ON"},
        {"type": "button", "action": "OFF", "label": "Turn OFF"},
    ]

    msg = {
        "type": "ui_definition",
        "sender_id": DEVICE_ID,
        "payload": {
            "ui": ui
        }
    }
    print("SEND: ui_definition", msg)
    send_json(sock, msg)


def send_state(sock, light_on: bool):
    """
    Send the current state of the device to the server.
    For the light device, the state is whether the light is on or off.
    """
    msg = {
        "type": "device_state",
        "sender_id": DEVICE_ID,
        "payload": {
            "state": {          
                "lightOn": light_on
            }
        }
    }
    print("SEND: device_state", msg)
    send_json(sock, msg)


def handle_action(sock, msg, light_on: bool) -> bool:
    """
    Handle an action received from the server.
    Updates the internal state based on the action (ON / OFF)
    and sends the updated state back to the server.
    """
    payload = msg.get("payload", {})
    action = payload.get("action")

    print("RECV: action", action)

    if action == "ON":
        light_on = True
    elif action == "OFF":
        light_on = False
    else:
        print("Unknown action:", action)
        return light_on

    # Send updated state back to the server
    send_state(sock, light_on)
    return light_on


def main():
    # 1) Connect to the server
    sock = socket.socket()
    sock.connect((SERVER_HOST, SERVER_PORT))
    print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")

    # Create a buffered reader for line-based JSON messages
    f = sock.makefile("r", encoding="utf-8", newline="\n")

    # 2) Register this device with the server
    send_register_device(sock)

    # 3) Send UI definition (buttons)
    send_ui_definition(sock)

    # 4) Send initial state (light is off)
    light_on = False
    send_state(sock, light_on)

    # 5) Main loop: wait for actions from the server
    try:
        while True:
            msg = recv_json_line(f)
            if msg is None:
                print("Server disconnected.")
                break

            msg_type = msg.get("type")
            print("RECV:", msg_type, msg)

            if msg_type == "action":
                light_on = handle_action(sock, msg, light_on)
            else:
                # For iteration 1, the device only reacts to "action" messages
                print("Ignoring message type:", msg_type)

    except KeyboardInterrupt:
        print("Shutting down device...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
