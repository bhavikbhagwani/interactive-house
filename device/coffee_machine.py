import socket, time
from protocol import send_json, recv_json_line
#	Coffee machine
#o	State: { isMaking: true/false }
#o	UI: Make button
#o	When MAKE is pressed:
#	isMaking = true
#	Simulate delay (e.g., 30 seconds)
#	Then set isMaking = false
#o	When isMaking = true:
#	Disable MAKE button ###

SERVER_HOST = "localhost"
SERVER_PORT = 5001

# Unique identifier for this device
DEVICE_ID = "coffee-machine-1"

def send_register_device(sock):
    """
    Inform the server that this client is a device.
    This message is sent once when the device connects.
    """
    msg = {
        "type": "register_device",
        "sender_id": DEVICE_ID,          
        "payload": {
            "deviceType": "coffee_machine"
        }
    }
    print("SEND: register_device", msg)
    send_json(sock, msg)


def send_ui_definition(sock, is_making: bool):
    """
    Send the UI definition to the server.
    The device defines which controls it supports (MAKE / STOP buttons).
    The unit will later render this UI.
    """
    ui = [
        {
        "type": "button",
        "action": "MAKE",
        "label": "Make coffee",
        "enabled": (not is_making)
    }
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


def send_state(sock, is_making: bool):
    """
    Send the current state of the device to the server.
    For the coffee machine device, the state is whether the coffee machine is making or not.
    """
    msg = {
        "type": "device_state",
        "sender_id": DEVICE_ID,
        "payload": {
            "state": {          
                "isMaking": is_making
            }
        }
    }
    print("SEND: device_state", msg)
    send_json(sock, msg)

def handle_action(sock, msg, is_making: bool) -> bool:
    """
    Handle an action received from the server.
    Updates the internal state based on the action (MAKE)
    and sends the updated state back to the server.
    """
    payload = msg.get("payload", {})
    action = payload.get("action")

    print("RECV: action", action)

    if action != "MAKE":
        print("Unknown action: ", action)
        return is_making
    
    if is_making:
        send_state(sock, is_making)
        send_ui_definition(sock, is_making)
        return is_making
    
    # Make coffee
    is_making = True
    send_state(sock, is_making)
    send_ui_definition(sock, is_making)

    print("Brewing coffee...")
    for a in range(30):
        time.sleep(1)
        print(a + 1)

    # Coffee is done
    is_making = False
    send_state(sock, is_making)
    send_ui_definition(sock, is_making)

    print("Coffee is done.")
    return is_making

def connect_with_retry(host, port, retry_seconds=2):
    while True:
        try:
            sock = socket.socket()
            sock.connect((host, port))
            return sock
        except ConnectionRefusedError:
            print(f"Server not up yet at {host}:{port}. Retrying in {retry_seconds}s...")
            time.sleep(retry_seconds)
        except OSError as e:
            print(f"Connect failed ({e}). Retrying in {retry_seconds}s...")
            time.sleep(retry_seconds)

def main():
    # 1) Connect to the server
    sock = connect_with_retry(SERVER_HOST, SERVER_PORT)
    print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")

    # Create a buffered reader for line-based JSON messages
    f = sock.makefile("r", encoding="utf-8", newline="\n")

    # 2) Register this device with the server
    send_register_device(sock)

    # 3) Send UI definition (buttons)
    send_ui_definition(sock, is_making=False)

    # 4) Send initial state (coffee machine is done)
    is_making = False
    send_state(sock, is_making)

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
                is_making = handle_action(sock, msg, is_making)
            else:
                # For iteration 1, the device only reacts to "action" messages
                print("Ignoring message type:", msg_type)

    except KeyboardInterrupt:
        print("Shutting down device...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()