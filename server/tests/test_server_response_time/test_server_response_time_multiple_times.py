import socket
import json
import time

HOST = "127.0.0.1"
PORT = 5001


def send_json(sock, message):
    sock.sendall((json.dumps(message) + "\n").encode("utf-8"))


def receive_json(sock):
    return sock.recv(4096).decode("utf-8").strip()


def test_response_time():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        # 1. Login first
        login_message = {
            "type": "login",
            "sender_id": "test-client",
            "payload": {
                "email": "primary@email.com",
                "password": "primary123"
            }
        }

        send_json(s, login_message)
        login_response = receive_json(s)

        print("Login response:", login_response)

        # 2. Now test get_devices response time
        test_message = {
            "type": "get_devices",
            "sender_id": "test-client",
            "payload": {}
        }

        start_time = time.time()

        send_json(s, test_message)
        response = receive_json(s)

        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        return response_time_ms, response


for i in range(10):
    response_time, response = test_response_time()

    print(f"Test {i+1}: {response_time:.2f} ms")
    print("Response:", response)
    print("-" * 40)

    time.sleep(1)