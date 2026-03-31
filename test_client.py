import time
import socket
import json

HOST = "127.0.0.1"
PORT = 5001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))


def send(msg):
    data = json.dumps(msg) + "\n"
    sock.sendall(data.encode())


def receive():
    sock.settimeout(0.5)
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            print("RESPONSE:", data.decode().strip())
    except:
        pass

# ✅ 1. LOGIN (VALID)
send({
    "type": "login",
    "sender_id": "client-1",
    "payload": {
        "email": "user@email.com",
        "password": "user123"
    }
})
receive()


# ✅ 2. GET DEVICES
send({
    "type": "get_devices",
    "sender_id": "client-1",
    "payload": {}
})
time.sleep(0.2)
receive()


# ✅ 3. GET UI
send({
    "type": "get_ui",
    "sender_id": "client-1",
    "payload": {
        "deviceId": "led-1"
    }
})
time.sleep(0.2)
receive()


# ✅ 4. VALID ACTION
send({
    "type": "action",
    "sender_id": "client-1",
    "payload": {
        "deviceId": "led-1",
        "action": "ON"
    }
})
receive()


# ❌ 5. INVALID TYPE (VALIDATION TEST)
send({
    "type": "hack",
    "sender_id": "client-1",
    "payload": {}
})
time.sleep(0.2)
receive()


# ❌ 6. MISSING FIELD (VALIDATION TEST)
send({
    "type": "login",
    "sender_id": "client-1",
    "payload": {
        "email": "user@email.com"
    }
})
time.sleep(0.2)
receive()


# ❌ 7. WRONG ACTION FORMAT
send({
    "type": "action",
    "sender_id": "client-1",
    "payload": {
        "deviceId": "led-1"
    }
})
time.sleep(0.2)
receive()


# 🔄 KEEP LISTENING
print("\nListening for updates...\n")
while True:
    if not receive():
        break