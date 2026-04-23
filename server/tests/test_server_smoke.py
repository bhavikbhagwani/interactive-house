
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import socket
import uuid
from protocol import send_json, recv_json_line

HOST = "127.0.0.1"
PORT = 5001


def open_connection():
    sock = socket.socket()
    sock.connect((HOST, PORT))
    buffered = sock.makefile("r", encoding="utf-8", newline="\n")
    return sock, buffered


def close_connection(sock, buffered):
    try:
        buffered.close()
    except Exception:
        pass
    try:
        sock.close()
    except Exception:
        pass


def print_result(name, passed, response=None):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if response is not None:
        print("   Response:", response)


def test_get_devices_without_login():
    sock, buffered = open_connection()
    try:
        send_json(sock, {
            "type": "get_devices",
            "sender_id": "test-unit-1",
            "payload": {}
        })
        response = recv_json_line(buffered)

        passed = (
            response is not None
            and response.get("type") == "error"
            and response.get("payload", {}).get("message") == "Please login first"
        )

        print_result("get_devices without login", passed, response)
        return passed
    finally:
        close_connection(sock, buffered)


def test_login_success():
    sock, buffered = open_connection()
    try:
        send_json(sock, {
            "type": "login",
            "sender_id": "test-unit-2",
            "payload": {
                "email": "user@email.com",
                "password": "user123"
            }
        })
        response = recv_json_line(buffered)

        passed = (
            response is not None
            and response.get("type") == "login_ok"
            and response.get("payload", {}).get("message") == "Login successful"
        )

        print_result("login success", passed, response)
        return passed
    finally:
        close_connection(sock, buffered)


def test_login_failure():
    sock, buffered = open_connection()
    try:
        send_json(sock, {
            "type": "login",
            "sender_id": "test-unit-3",
            "payload": {
                "email": "user@email.com",
                "password": "wrongpassword"
            }
        })
        response = recv_json_line(buffered)

        passed = (
            response is not None
            and response.get("type") == "login_failed"
            and response.get("payload", {}).get("message") == "Invalid email or password"
        )

        print_result("login failure", passed, response)
        return passed
    finally:
        close_connection(sock, buffered)


def test_get_devices_after_login():
    sock, buffered = open_connection()
    try:
        send_json(sock, {
            "type": "login",
            "sender_id": "test-unit-4",
            "payload": {
                "email": "user@email.com",
                "password": "user123"
            }
        })
        login_response = recv_json_line(buffered)

        if not login_response or login_response.get("type") != "login_ok":
            print_result("get_devices after login", False, login_response)
            return False

        send_json(sock, {
            "type": "get_devices",
            "sender_id": "test-unit-4",
            "payload": {}
        })
        response = recv_json_line(buffered)

        passed = (
            response is not None
            and response.get("type") == "device_list"
            and "devices" in response.get("payload", {})
        )

        print_result("get_devices after login", passed, response)
        return passed
    finally:
        close_connection(sock, buffered)


def test_unknown_message_type():
    sock, buffered = open_connection()
    try:
        send_json(sock, {
            "type": "totally_unknown_type",
            "sender_id": "test-unit-5",
            "payload": {}
        })
        response = recv_json_line(buffered)

        passed = (
            response is not None
            and response.get("type") == "error"
            and "Unknown message type" in response.get("payload", {}).get("message", "")
        )

        print_result("unknown message type", passed, response)
        return passed
    finally:
        close_connection(sock, buffered)


def test_get_ui_unknown_device():
    sock, buffered = open_connection()
    try:
        send_json(sock, {
            "type": "login",
            "sender_id": "test-unit-6",
            "payload": {
                "email": "user@email.com",
                "password": "user123"
            }
        })
        login_response = recv_json_line(buffered)

        if not login_response or login_response.get("type") != "login_ok":
            print_result("get_ui unknown device", False, login_response)
            return False

        fake_device_id = f"unknown-{uuid.uuid4().hex[:8]}"

        send_json(sock, {
            "type": "get_ui",
            "sender_id": "test-unit-6",
            "payload": {
                "deviceId": fake_device_id
            }
        })
        response = recv_json_line(buffered)

        passed = (
            response is not None
            and response.get("type") == "error"
            and fake_device_id in response.get("payload", {}).get("message", "")
        )

        print_result("get_ui unknown device", passed, response)
        return passed
    finally:
        close_connection(sock, buffered)


def main():
    print("Running smoke tests against the server...\n")

    tests = [
        test_get_devices_without_login,
        test_login_success,
        test_login_failure,
        test_get_devices_after_login,
        test_unknown_message_type,
        test_get_ui_unknown_device,
    ]

    passed_count = 0

    for test_func in tests:
        try:
            if test_func():
                passed_count += 1
        except Exception as e:
            print_result(test_func.__name__, False, {"exception": str(e)})

    total = len(tests)
    print(f"\nSummary: {passed_count}/{total} tests passed.")


if __name__ == "__main__":
    main()