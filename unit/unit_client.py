import argparse
import socket
import threading
import json
import sys
from protocol import send_json, recv_json_line

# Configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5001
UNIT_ID = "unit-1"

# State
devices = []
selected_device_id = None
ui_items = []
latest_state = {}


def handle_message(msg):
    """Handle incoming messages from the server."""
    global devices, selected_device_id, ui_items, latest_state
    
    msg_type = msg.get("type")
    payload = msg.get("payload", {})
    
    print(f"\nRECV: {msg_type}", flush=True)
    
    if msg_type == "device_list":
        devices = payload.get("devices", [])
        print(f" - {len(devices)} devices")
        print("\nAvailable devices:")
        for i, dev in enumerate(devices, 1):
            print(f"  [{i}] {dev.get('deviceId')} ({dev.get('deviceType')})")
        print()
    
    
    elif msg_type == "ui_definition":
        device_id = payload.get("deviceId")
        ui_items = payload.get("ui", [])
        state = payload.get("state")
        if state:
            latest_state.update(state)
            print(f"Current state: {latest_state}")
        print(f" - deviceId={device_id}, {len(ui_items)} UI items")
        print(f"\nUI for device: {device_id}")
        render_ui()
    
    
    elif msg_type == "state_update":
        device_id = payload.get("deviceId")
        state = payload.get("state", {})
        latest_state.update(state)
        print(f" - deviceId={device_id}, state={state}")
        print(f"Current state: {latest_state}")
        if selected_device_id:
            print("\nUI:")
            render_ui()
    
    else:
        print(f" - {payload}")
    print("\n> ", end="", flush=True)


def render_ui():
    """Render the UI items as a CLI menu."""
    for i, item in enumerate(ui_items, 1):
        if item.get("type") == "button":
            label = item.get("label", "")
            action = item.get("action", "")
            print(f"  [{i}] {label} (action={action})")
    print("  [b] Back to device list")
    print("  [q] Quit")
    print()


def receiver_thread(file_like):
    """Background thread that continuously receives messages."""
    try:
        while True:
            msg = recv_json_line(file_like)
            if msg is None:
                print("\nServer disconnected.")
                sys.exit(0)
            handle_message(msg)
    except Exception as e:
        print(f"\nReceiver error: {e}")
        sys.exit(1)


def run_interactive(host, port):
    """Run the interactive session."""
    global selected_device_id, ui_items, latest_state
    
    try:
        # Connect to server
        print(f"Connecting to {host}:{port}...")
        sock = socket.create_connection((host, port))
        f = sock.makefile("r", encoding="utf-8", newline="\n")
        print("Connected!")
        
        # Start receiver thread
        thread = threading.Thread(target=receiver_thread, args=(f,), daemon=True)
        thread.start()
        
        # Send login
        login_msg = {
            "type": "login",
            "sender_id": UNIT_ID,
            "payload": {"username": "user", "password": "1234"}
        }
        print(f"SEND: login")
        send_json(sock, login_msg)
        
        # Send get_devices
        get_devices_msg = {
            "type": "get_devices",
            "sender_id": UNIT_ID,
            "payload": {}
        }
        print(f"SEND: get_devices")
        send_json(sock, get_devices_msg)
        
        # Main interaction loop
        while True:
            try:
                user_input = input("").strip()
                
                if user_input.lower() == "q":
                    print("Quitting...")
                    sock.close()
                    break
                
                elif user_input.lower() == "b":
                    # Back to device list
                    selected_device_id = None
                    ui_items = []
                    latest_state = {}
                    get_devices_msg = {
                        "type": "get_devices",
                        "sender_id": UNIT_ID,
                        "payload": {}
                    }
                    print(f"SEND: get_devices")
                    send_json(sock, get_devices_msg)
                
                elif user_input.isdigit():
                    choice = int(user_input)
                    
                    if selected_device_id is None:
                        # Selecting a device
                        if 1 <= choice <= len(devices):
                            selected_device_id = devices[choice - 1]["deviceId"]
                            latest_state = {}
                            get_ui_msg = {
                                "type": "get_ui",
                                "sender_id": UNIT_ID,
                                "payload": {"deviceId": selected_device_id}
                            }
                            print(f"SEND: get_ui - deviceId={selected_device_id}")
                            send_json(sock, get_ui_msg)
                        else:
                            print("Invalid device number.")
                    
                    else:
                        # Selecting a UI action
                        if 1 <= choice <= len(ui_items):
                            item = ui_items[choice - 1]
                            if item.get("type") == "button":
                                action = item.get("action")
                                action_msg = {
                                    "type": "action",
                                    "sender_id": UNIT_ID,
                                    "payload": {
                                        "deviceId": selected_device_id,
                                        "action": action
                                    }
                                }
                                print(f"SEND: action - deviceId={selected_device_id}, action={action}")
                                send_json(sock, action_msg)
                        else:
                            print("Invalid UI option.")
                
                else:
                    print("Invalid input. Enter a number, 'b' for back, or 'q' to quit.")
            
            except KeyboardInterrupt:
                print("\nQuitting...")
                sock.close()
                break
    
    except ConnectionRefusedError:
        print("Connection refused. Server not running yet.")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Unit CLI client")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port number")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    subparsers.add_parser("run", help="Run interactive session")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_interactive(args.host, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()