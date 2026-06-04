import socket
import json
import time

HOST = "127.0.0.1"
PORT = 5001

EMAIL = "primary@email.com"
PASSWORD = "primary123"

DEVICE_ID = "light-1"


def send_json(sock, message):
    sock.sendall((json.dumps(message) + "\n").encode("utf-8"))


def receive_json(sock):
    data = sock.recv(4096).decode("utf-8").strip()
    return json.loads(data)


def login(sock):
    login_message = {
        "type": "login",
        "sender_id": "test-client",
        "payload": {
            "email": EMAIL,
            "password": PASSWORD
        }
    }

    start_time = time.time()
    send_json(sock, login_message)
    response = receive_json(sock)
    end_time = time.time()

    return (end_time - start_time) * 1000, response


def measure_action_latency(sock, light_state):
    action_message = {
        "type": "action",
        "sender_id": "test-client",
        "payload": {
            "deviceId": DEVICE_ID,
            "action": "ON" if light_state else "OFF"
        }
    }

    start_time = time.time()
    send_json(sock, action_message)

    while True:
        response = receive_json(sock)
        print("Received:", response)

        if response.get("type") in ["device_state", "action_ok", "state_update"]:
            payload = response.get("payload", {})

            if payload.get("deviceId") == DEVICE_ID:
                state = payload.get("state", {})

                if state.get("lightOn") == light_state:
                    end_time = time.time()
                    return (end_time - start_time) * 1000, response


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    login_latency, login_response = login(s)

    print(f"Login latency: {login_latency:.2f} ms")
    print("Login response:", login_response)
    print("-" * 50)

    for i in range(10):
        light_state = i % 2 == 0

        action_latency, final_response = measure_action_latency(s, light_state)

        print(f"Test {i + 1}: Light set to {light_state}")
        print(f"Action/state-update latency: {action_latency:.2f} ms")
        print("-" * 50)

        time.sleep(1)