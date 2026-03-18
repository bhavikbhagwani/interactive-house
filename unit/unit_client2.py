import json
import socket

# This is a simple test client that connects to the server, logs in, retrieves the device list, and allows the user to send actions to the devices via a command-line menu. :) This won't be needed in the final system, but it's useful for testing the server and hardware bridge without a full UI.

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
SENDER_ID = "test-unit"
EMAIL = "user@email.com"
PASSWORD = "user123"


def send(sock, msg):
    sock.sendall((json.dumps(msg) + "\n").encode())


def recv_line(file_obj):
    line = file_obj.readline()
    if not line:
        return None
    return line.strip()


def send_action(sock, file_obj, device_id, action):
    send(sock, {
        "type": "get_ui",
        "sender_id": SENDER_ID,
        "payload": {"deviceId": device_id}
    })
    ui_response = recv_line(file_obj)
    if ui_response is not None:
        print(ui_response)

    send(sock, {
        "type": "action",
        "sender_id": SENDER_ID,
        "payload": {"deviceId": device_id, "action": action}
    })
    print(f"Sent {action} to {device_id}")

    action_response = recv_line(file_obj)
    if action_response is not None:
        print(action_response)


def print_menu():
    print("\nChoose an action:")
    print("1. LED 1 ON")
    print("2. LED 1 OFF")
    print("3. LED 2 ON")
    print("4. LED 2 OFF")
    print("5. Fan ON")
    print("6. Fan OFF")
    print("7. Window OPEN")
    print("8. Window CLOSE")
    print("9. Door OPEN")
    print("10. Door CLOSE")
    print("11. Door STOP")
    print("q. Quit")


def main():
    sock = socket.create_connection((SERVER_HOST, SERVER_PORT))
    file_obj = sock.makefile("r", encoding="utf-8", newline="\n")

    try:
        send(sock, {
            "type": "login",
            "sender_id": SENDER_ID,
            "payload": {"email": EMAIL, "password": PASSWORD}
        })
        print(recv_line(file_obj))

        send(sock, {
            "type": "get_devices",
            "sender_id": SENDER_ID,
            "payload": {}
        })
        print(recv_line(file_obj))

        while True:
            print_menu()
            choice = input("> ").strip().lower()

            if choice == "1":
                send_action(sock, file_obj, "led-1", "ON")
            elif choice == "2":
                send_action(sock, file_obj, "led-1", "OFF")
            elif choice == "3":
                send_action(sock, file_obj, "led-2", "ON")
            elif choice == "4":
                send_action(sock, file_obj, "led-2", "OFF")
            elif choice == "5":
                send_action(sock, file_obj, "fan-1", "ON")
            elif choice == "6":
                send_action(sock, file_obj, "fan-1", "OFF")
            elif choice == "7":
                send_action(sock, file_obj, "servo-1", "OPEN")
            elif choice == "8":
                send_action(sock, file_obj, "servo-1", "CLOSE")
            elif choice == "9":
                send_action(sock, file_obj, "door-1", "OPEN")
            elif choice == "10":
                send_action(sock, file_obj, "door-1", "CLOSE")
            elif choice == "11":
                send_action(sock, file_obj, "door-1", "STOP")
            elif choice == "q":
                break
            else:
                print("Invalid choice.")
    finally:
        try:
            file_obj.close()
        except Exception:
            pass
        sock.close()


if __name__ == "__main__":
    main()
