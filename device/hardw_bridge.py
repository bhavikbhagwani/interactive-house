
"""
Hardware Bridge - Connects server to Arduino devices such as LEDs and a servo(window). RUN this in the terminal along with server.py and unit_client2.py to test the full system. :)
RUN ORDER:
    1. Start the server: python server.py
    2. Start the hardware bridge: python hardw_bridge.py --simulate  (or without --simulate if you have an Arduino connected and then it will run on port COM6 - check the COM port)
    3. Start the test client: python unit_client2.py

Usage:
    python hardw_bridge.py --simulate         # Without Arduino
    python hardw_bridge.py --port COM6        # With Arduino (Windows) - check the COM port
    python hardw_bridge.py --port /dev/ttyUSB0  # With Arduino (Linux)

"""

import socket
import threading
import argparse
import time
import sys
from protocol import send_json, recv_json_line

# CONFIGURATION
SERVER_HOST = "localhost"
SERVER_PORT = 5001

LED_DEVICES = [
    {"id": "led-1", "name": "LED 1", "pin": 13},
    {"id": "led-2", "name": "LED 2", "pin": 5},
]

FAN_DEVICES = [
    {"id": "fan-1", "name": "Fan", "pin": 6},
]

#window
SERVO_DEVICES = [
    {"id": "servo-1", "name": "Window Servo", "pin": 10, "open_angle": 90, "close_angle": 0},
]

#door
DOOR_DEVICES = [
    {"id": "door-1", "name": "Door", "pin": 9, "open_angle": 180, "close_angle": 0},
]

# Motion Sensor
MOTION_SENSOR_DEVICE = [
    {"id": "motion-sensor-1", "name": "Motion Sensor", "pin": 2},
]

DEFAULT_SERIAL_PORT = "COM5"
SERIAL_BAUD_RATE = 9600

# ARDUINO SERIAL COMMUNICATION
class ArduinoSerial:
    def __init__(self, port: str, simulate: bool = False):
        self.port = port
        self.simulate = simulate
        self.serial = None
        self.lock = threading.Lock()
        # Listen to Arduino in the background
        self.event_callback = None
        self.reader_thread = None
        self.reader_running = False
        
        if not simulate:
            try:
                import serial
                self.serial = serial.Serial(port, SERIAL_BAUD_RATE, timeout=1)
                time.sleep(2)
                print(f"[Arduino] Connected to {port}")
            except Exception as e:
                print(f"[Arduino] ERROR: Could not connect to {port}: {e}")
                print("[Arduino] Starta igen med korrekt --port eller använd --simulate om du vill testa utan hårdvara.")
                raise
        else:
            print("[Arduino] Running in SIMULATION mode")
    
    def _send_command(self, command: str) -> bool:
        with self.lock:
            if self.simulate:
                print(f"[Arduino SIM] {command.strip()}")
                return True

            try:
                self.serial.write(command.encode())
                print(f"[Arduino TX] {command.strip()}")
                return True
            except Exception as e:
                print(f"[Arduino] Error sending command: {e}")
                return False

#LED
    def send_led_command(self, pin: int, state: bool) -> bool:
        state_str = "ON" if state else "OFF"
        command = f"LED:{pin}:{state_str}\n"
        return self._send_command(command)

#window
    def send_servo_command(self, pin: int, angle: int) -> bool:
        command = f"SERVO:{pin}:{angle}\n"
        return self._send_command(command)

    def send_fan_command(self, pin: int, state: bool) -> bool:
        state_str = "ON" if state else "OFF"
        command = f"FAN:{pin}:{state_str}\n"
        return self._send_command(command)
    
    def send_door_command(self, pin: int, state: str) -> bool:
        command = f"DOOR:{pin}:{state}\n"
        return self._send_command(command)
    def set_event_callback(self, callback):
        self.event_callback = callback

    def start_reader(self):
        if self.simulate or not self.serial:
            return
        self.reader_running = True
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def _reader_loop(self):
        while self.reader_running:
            try:
                line = self.serial.readline().decode(errors="ignore").strip()
                if not line:
                    continue

                print(f"[Arduino RX] {line}")

                if line.startswith("MOTION:") and self.event_callback:
                    self.event_callback(line)
                elif line.startswith("OK:"):
                    print(f"[Arduino OK] {line}")
                elif line.startswith("ERR:"):
                    print(f"[Arduino ERR] {line}")

            except Exception as e:
                print(f"[Arduino] Reader error: {e}")
                break
    
    # Background listening is shutdown when brige is closed.
    def close(self):
        self.reader_running = False
        if self.serial:
            self.serial.close()

class BaseDevice:
    def __init__(self, device_id: str, name: str, pin: int, arduino: ArduinoSerial):
        self.device_id = device_id
        self.name = name
        self.pin = pin
        self.arduino = arduino
        self.sock = None
        self.running = False
    
    def connect(self, host: str, port: int):
        while True:
            try:
                self.sock = socket.socket()
                self.sock.connect((host, port))
                print(f"[{self.device_id}] Connected to server")
                return
            except ConnectionRefusedError:
                print(f"[{self.device_id}] Server not ready, retrying...")
                time.sleep(2)
            except OSError as e:
                print(f"[{self.device_id}] Connection failed ({e}), retrying...")
                time.sleep(2)
    
    def send_register(self):
        raise NotImplementedError

    def send_ui_definition(self):
        raise NotImplementedError

    def send_state(self):
        raise NotImplementedError

    def handle_action(self, action: str):
        raise NotImplementedError

    def run(self):
        self.running = True
        f = self.sock.makefile("r", encoding="utf-8", newline="\n")

        try:
            while self.running:
                msg = recv_json_line(f)
                if msg is None:
                    print(f"[{self.device_id}] Server disconnected")
                    break

                msg_type = msg.get("type")
                if msg_type == "action":
                    action = msg.get("payload", {}).get("action")
                    self.handle_action(action)
        except Exception as e:
            print(f"[{self.device_id}] Error: {e}")
        finally:
            self.sock.close()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()


class LEDDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, arduino: ArduinoSerial):
        super().__init__(device_id, name, pin, arduino)
        self.state = False

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "led"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as LED device")
    
    def send_ui_definition(self):
        ui = [
            {"type": "button", "action": "ON", "label": f"{self.name} ON"},
            {"type": "button", "action": "OFF", "label": f"{self.name} OFF"},
        ]
        msg = {
            "type": "ui_definition",
            "sender_id": self.device_id,
            "payload": {"ui": ui}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Sent UI definition")
    
    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {"state": {"ledOn": self.state}}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] State: {'ON' if self.state else 'OFF'}")
    
    def handle_action(self, action: str):
        if action == "ON":
            new_state = True
        elif action == "OFF":
            new_state = False
        else:
            print(f"[{self.device_id}] Unknown action: {action}")
            return

        success = self.arduino.send_led_command(self.pin, new_state)
        if success:
            self.state = new_state
            self.send_state()


class ServoDevice(BaseDevice):
    def __init__(
        self,
        device_id: str,
        name: str,
        pin: int,
        open_angle: int,
        close_angle: int,
        arduino: ArduinoSerial,
    ):
        super().__init__(device_id, name, pin, arduino)
        self.open_angle = open_angle
        self.close_angle = close_angle
        self.position = close_angle

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "servo"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as servo device")

    def send_ui_definition(self):
        ui = [
            {"type": "button", "action": "OPEN", "label": f"{self.name} OPEN"},
            {"type": "button", "action": "CLOSE", "label": f"{self.name} CLOSE"},
        ]
        msg = {
            "type": "ui_definition",
            "sender_id": self.device_id,
            "payload": {"ui": ui}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Sent UI definition")

    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {"state": {"position": self.position}}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Position: {self.position}")

    def handle_action(self, action: str):
        if action == "OPEN":
            angle = self.open_angle
        elif action == "CLOSE":
            angle = self.close_angle
        else:
            print(f"[{self.device_id}] Unknown action: {action}")
            return

        if not 0 <= angle <= 180:
            print(f"[{self.device_id}] Invalid angle: {angle}")
            return

        success = self.arduino.send_servo_command(self.pin, angle)
        if success:
            self.position = angle
            self.send_state()

class DoorDevice(BaseDevice):
    def __init__(
        self,
        device_id: str,
        name: str,
        pin: int,
        open_angle: int,
        close_angle: int,
        arduino: ArduinoSerial,
    ):
        super().__init__(device_id, name, pin, arduino)
        self.open_angle = open_angle
        self.close_angle = close_angle
        self.position = close_angle

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "door"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as door device")

    def send_ui_definition(self):
        ui = [
            {"type": "button", "action": "OPEN", "label": f"{self.name} OPEN"},
            {"type": "button", "action": "CLOSE", "label": f"{self.name} CLOSE"},
            {"type": "button", "action": "STOP", "label": f"{self.name} STOP"},
        ]
        msg = {
            "type": "ui_definition",
            "sender_id": self.device_id,
            "payload": {"ui": ui}
        }
        send_json(self.sock, msg)

    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {"state": {"doorState": self.position}}
        }
        send_json(self.sock, msg)

    def handle_action(self, action: str):
        if action == "OPEN":
            state = "OPEN"
        elif action == "CLOSE":
            state = "CLOSE"
        elif action == "STOP":
            state = "STOP"
        else:
            return

        success = self.arduino.send_door_command(self.pin, state)
        if success:
            self.position = state
            self.send_state()

class FanDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, arduino: ArduinoSerial):
        super().__init__(device_id, name, pin, arduino)
        self.state = False

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "fan"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as fan device")

    def send_ui_definition(self):
        ui = [
            {"type": "button", "action": "ON", "label": f"{self.name} ON"},
            {"type": "button", "action": "OFF", "label": f"{self.name} OFF"},
        ]
        msg = {
            "type": "ui_definition",
            "sender_id": self.device_id,
            "payload": {"ui": ui}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Sent UI definition")

    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {"state": {"fanOn": self.state}}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] State: {'ON' if self.state else 'OFF'}")

    def handle_action(self, action: str):
        if action == "ON":
            new_state = True
        elif action == "OFF":
            new_state = False
        else:
            print(f"[{self.device_id}] Unknown action: {action}")
            return

        success = self.arduino.send_fan_command(self.pin, new_state)
        if success:
            self.state = new_state
            self.send_state()


class MotionSensorDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, arduino: ArduinoSerial):
        super().__init__(device_id, name, pin, arduino)
        self.motion_detected = False

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "motion_sensor"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as motion sensor device")

    def send_ui_definition(self):
 
        msg = {
            "type": "ui_definition",
            "sender_id": self.device_id,
            "payload": {"ui": []}
        }
        send_json(self.sock, msg)
        # print(f"[{self.device_id}] Sent UI definition")

    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {"state": {"motionDetected": self.motion_detected}}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Motion: {self.motion_detected}")

    def handle_action(self, action: str):
        print(f"[{self.device_id}] Motion sensor does not support actions")


# HARDWARE BRIDGE
class HardwareBridge:
    def __init__(self, serial_port: str, simulate: bool = False):
        self.arduino = ArduinoSerial(serial_port, simulate)
        self.devices = []
        self.threads = []
        
        for config in LED_DEVICES:
            device = LEDDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                arduino=self.arduino
            )
            self.devices.append(device)

        for config in FAN_DEVICES:
            device = FanDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                arduino=self.arduino
            )
            self.devices.append(device)

        for config in SERVO_DEVICES:
            device = ServoDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                open_angle=config["open_angle"],
                close_angle=config["close_angle"],
                arduino=self.arduino
            )
            self.devices.append(device)

        for config in DOOR_DEVICES:
            device = DoorDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                open_angle=config["open_angle"],
                close_angle=config["close_angle"],
                arduino=self.arduino
            )
            self.devices.append(device)
        
        for config in MOTION_SENSOR_DEVICE:
            device = MotionSensorDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                arduino=self.arduino
            )
            self.devices.append(device)
            self.motion_device = next(
            (device for device in self.devices if isinstance(device, MotionSensorDevice)),
            None
        )

        self.arduino.set_event_callback(self.handle_arduino_event)

    def handle_arduino_event(self, line: str):
        if not self.motion_device:
            return

        if line == "MOTION:1":
            self.motion_device.motion_detected = True
            self.motion_device.send_state()

        elif line == "MOTION:0":
            self.motion_device.motion_detected = False
            self.motion_device.send_state()
                        
    def start(self, host: str, port: int):
        print(f"\n{'='*50}")
        print("Hardware Bridge Starting")
        print(f"Server: {host}:{port}")
        print(f"Devices: {len(self.devices)}")
        print(f"{'='*50}\n")
        
        for device in self.devices:
            device.connect(host, port)
            device.send_register()
            device.send_ui_definition()
            device.send_state()

        self.arduino.start_reader()
        
        for device in self.devices:
            thread = threading.Thread(target=device.run, daemon=True)
            thread.start()
            self.threads.append(thread)
        
        print(f"\n[Bridge] All devices connected. Waiting for commands...\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        print("\n[Bridge] Shutting down...")
        for device in self.devices:
            device.stop()
        self.arduino.close()
        print("[Bridge] Goodbye!")


# MAIN
def main():
    parser = argparse.ArgumentParser(description="Hardware Bridge for Arduino LEDs and servo devices")
    parser.add_argument("--simulate", action="store_true", 
                        help="Run without Arduino (simulation mode)")
    parser.add_argument("--port", default=DEFAULT_SERIAL_PORT,
                        help=f"Serial port for Arduino (default: {DEFAULT_SERIAL_PORT})")
    parser.add_argument("--server", default=SERVER_HOST,
                        help=f"Server hostname (default: {SERVER_HOST})")
    parser.add_argument("--server-port", type=int, default=SERVER_PORT,
                        help=f"Server port (default: {SERVER_PORT})")
    
    args = parser.parse_args()

    try:
        bridge = HardwareBridge(serial_port=args.port, simulate=args.simulate)
        bridge.start(args.server, args.server_port)
    except Exception as e:
        print(f"[Bridge] Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
