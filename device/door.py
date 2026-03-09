import socket, time
from protocol import send_json, recv_json_line

SERVER_HOST = "localhost"
SERVER_PORT = 5001

DEVICE_ID = "door-1" #id

def send_register_device(sock):
    msg = {
        "type": "register_device",
        "sender_id": DEVICE_ID,
        "payload": {
            "deviceType": "door"
        }
    }
    print("SEND: register_device", msg)
    send_json(sock, msg)


def send_ui_definition(sock):
    ui = [
        {"type": "button", "action": "LOCK", "label": "Lock"},
        {"type": "button", "action": "UNLOCK", "label": "Unlock"},
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


def send_state(sock, locked: bool):
    msg = {
        "type": "device_state",
        "sender_id": DEVICE_ID,
        "payload": {
            "state": {
                "locked": locked
            }
        }
    }
    print("SEND: device_state", msg)
    send_json(sock, msg)


def handle_action(sock, msg, locked: bool) -> bool:
    payload = msg.get("payload", {})
    action = payload.get("action")

    print("RECV: action", action)

    if action == "LOCK":
        locked = True
    elif action == "UNLOCK":
        locked = False
    else:
        print("Unknown action:", action)
        return locked

    send_state(sock, locked)
    return locked


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
    sock = connect_with_retry(SERVER_HOST, SERVER_PORT)
    print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")

    f = sock.makefile("r", encoding="utf-8", newline="\n")

    send_register_device(sock)
    send_ui_definition(sock)

    locked = False  # initial state
    send_state(sock, locked)

    try:
        while True:
            msg = recv_json_line(f)
            if msg is None:
                print("Server disconnected.")
                break

            msg_type = msg.get("type")
            print("RECV:", msg_type, msg)

            if msg_type == "action":
                locked = handle_action(sock, msg, locked)
            else:
                print("Ignoring message type:", msg_type)

    except KeyboardInterrupt:
        print("Shutting down device...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
