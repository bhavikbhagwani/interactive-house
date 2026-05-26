import socket, time
from protocol import send_json

SERVER_HOST = "localhost"
SERVER_PORT = 5001

DEVICE_ID = "motion-1"

def send_register_device(sock):
    msg = {
        "type": "register_device",
        "sender_id": DEVICE_ID,
        "payload": {
            "deviceType": "motion_sensor"
        }
    }
    print("SEND: register_device", msg)
    send_json(sock, msg)


def send_state(sock, motion_detected: bool):
    msg = {
        "type": "device_state",
        "sender_id": DEVICE_ID,
        "payload": {
            "state": {
                "motionDetected": motion_detected
            }
        }
    }
    print("SEND: device_state", msg)
    send_json(sock, msg)


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

    send_register_device(sock)

    try:
        while True:
            # Simulerad motion sensor:
            send_state(sock, True)
            time.sleep(2)

            send_state(sock, False)
            time.sleep(5)

    except KeyboardInterrupt:
        print("Shutting down motion sensor...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()