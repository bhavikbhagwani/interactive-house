"""
Hardware Bridge - Connects server to Arduino devices such as LEDs, servo, sensors, and alarm.

RUN ORDER:
    1. Start the server: python server.py
    2. Start the hardware bridge: python hardw_bridge.py --simulate  (or without --simulate if you have an Arduino connected)
    3. Start the test client: python unit_client2.py

Usage:
    python hardw_bridge.py --simulate         # Without Arduino
    python hardw_bridge.py --port COM5        # With Arduino (Windows)
    python hardw_bridge.py --port /dev/ttyUSB0  # With Arduino (Linux)
"""

import socket
import threading
import argparse
import time
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

# Window servo
SERVO_DEVICES = [
    {"id": "servo-1", "name": "Window", "pin": 10, "open_angle": 90, "close_angle": 0},
]

# Door servo
DOOR_DEVICES = [
    {"id": "door-1", "name": "Door", "pin": 9, "open_angle": 180, "close_angle": 0},
]

# Motion Sensor (PIR)
# MOTION_SENSOR_DEVICES = [
#     {"id": "motion-sensor-1", "name": "Motion Sensor", "pin": 2},
# ]

SMOKE_SENSOR_DEVICES = [
    {"id": "smoke-sensor-1", "name": "Smoke Sensor", "pin": "A0", "threshold": 130},
]

TEMPERATURE_SENSOR_DEVICES = [
    {"id": "temp-sensor-1", "name": "Temperature Sensor", "pin": "A3", "threshold_high": 30, "threshold_low": 18},
]

# Alarm/Buzzer
ALARM_DEVICES = [
    {"id": "alarm-1", "name": "Alarm Buzzer", "pin": 3},  # Digital pin 3 (PWM for tone)
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
        self.event_callback = None
        self.reader_thread = None
        self.reader_running = False
        
        # Simulated sensor values
        self.sim_smoke_value = 100
        self.sim_temp_value = 22.0
        
        if not simulate:
            try:
                import serial
                self.serial = serial.Serial(port, SERIAL_BAUD_RATE, timeout=1)
                time.sleep(2)
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                print(f"[Arduino] Connected to {port}")
            except Exception as e:
                print(f"[Arduino] ERROR: Could not connect to {port}: {e}")
                print("[Arduino] Use --simulate if you want to test without hardware.")
                raise
        else:
            print("[Arduino] Running in SIMULATION mode")
    
    def _send_command(self, command: str) -> bool:
        with self.lock:
            if self.simulate:
                print(f"[Arduino SIM] {command.strip()}")
                return True

            try:
                self.serial.reset_input_buffer()
                self.serial.write(command.encode())
                self.serial.flush()

                response = ""
                for _ in range(5):
                    time.sleep(0.1)
                    response = self.serial.readline().decode(errors="replace").strip()
                    if response:
                        break

                print(f"[Arduino RAW] command={command.strip()} response={response!r}")

                if response.startswith("OK:"):
                    print(f"[Arduino] {command.strip()} -> {response}")
                    return True

                print(f"[Arduino] Unexpected response: {response}")
                return False
            except Exception as e:
                print(f"[Arduino] Error sending command: {e}")
                return False

    def _query_command(self, command: str) -> str:
        """Send a command and return the response value."""
        with self.lock:
            if self.simulate:
                # Return simulated values for sensor queries
                if command.startswith("READ_ANALOG:A0"):
                    return str(self.sim_smoke_value)
                elif command.startswith("READ_ANALOG:A3"):
                    return str(int(self.sim_temp_value * 10))
                return "0"

            try:
                self.serial.reset_input_buffer()
                self.serial.write(command.encode())
                self.serial.flush()

                response = ""
                for _ in range(5):
                    time.sleep(0.1)
                    response = self.serial.readline().decode(errors="replace").strip()
                    if response:
                        break

                print(f"[Arduino QUERY] command={command.strip()} response={response!r}")
                
                # Parse response like "VALUE:123"
                if response.startswith("VALUE:"):
                    parts = response.split(":")
                    return parts[-1]
                return response
            except Exception as e:
                print(f"[Arduino] Error querying: {e}")
                return "0"

    # LED commands
    def send_led_command(self, pin: int, state: bool) -> bool:
        state_str = "ON" if state else "OFF"
        command = f"LED:{pin}:{state_str}\n"
        return self._send_command(command)

    # Servo commands (window)
    def send_servo_command(self, pin: int, angle: int) -> bool:
        command = f"SERVO:{pin}:{angle}\n"
        return self._send_command(command)

    # Fan commands
    def send_fan_command(self, pin: int, state: bool) -> bool:
        state_str = "ON" if state else "OFF"
        command = f"FAN:{state_str}\n"
        return self._send_command(command)
    
    # Door commands
    def send_door_command(self, pin: int, state: str) -> bool:
        command = f"DOOR:{pin}:{state}\n"
        return self._send_command(command)

    # Alarm/Buzzer commands
    def send_alarm_command(self, pin: int, state: bool, frequency: int = 1000) -> bool:
        if state:
            command = f"ALARM:{pin}:ON:{frequency}\n"
        else:
            command = f"ALARM:{pin}:OFF\n"
        return self._send_command(command)

    # Read analog sensor value
    def read_analog(self, pin) -> int:
        command = f"READ_ANALOG:{pin}\n"
        result = self._query_command(command)
        try:
            return int(result)
        except ValueError:
            return 0

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

                if self.event_callback:
                    if line.startswith("MOTION:"):
                        self.event_callback(line)
                    elif line.startswith("SMOKE:"):
                        self.event_callback(line)
                    elif line.startswith("TEMP:"):
                        self.event_callback(line)
                elif line.startswith("OK:"):
                    print(f"[Arduino OK] {line}")
                elif line.startswith("ERR:"):
                    print(f"[Arduino ERR] {line}")

            except Exception as e:
                print(f"[Arduino] Reader error: {e}")
                break
    
    def close(self):
        self.reader_running = False
        if self.serial:
            self.serial.close()


# BASE DEVICE CLASS
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


# LED DEVICE
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
        action = action.upper()
        if action == "ON":
            new_state = True
        elif action == "OFF":
            new_state = False
        else:
            print(f"[{self.device_id}] Unknown action: {action}")
            return

        success = self.arduino.send_led_command(self.pin, new_state)
        print(f"[{self.device_id}] command success = {success}")

        self.state = new_state
        self.send_state()


# SERVO DEVICE (Window)
class ServoDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, open_angle: int, close_angle: int, arduino: ArduinoSerial):
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
        action = action.upper()
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
        print(f"[{self.device_id}] command success = {success}")

        self.position = angle
        self.send_state()


# DOOR DEVICE
class DoorDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, open_angle: int, close_angle: int, arduino: ArduinoSerial):
        super().__init__(device_id, name, pin, arduino)
        self.open_angle = open_angle
        self.close_angle = close_angle
        self.position = "CLOSE"

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
        print(f"[{self.device_id}] Sent UI definition")

    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {"state": {"doorState": self.position}}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Position: {self.position}")

    def handle_action(self, action: str):
        action = action.upper()
        if action == "OPEN":
            state = "OPEN"
        elif action == "CLOSE":
            state = "CLOSE"
        elif action == "STOP":
            state = "STOP"
        else:
            return

        success = self.arduino.send_door_command(self.pin, state)
        print(f"[{self.device_id}] command success = {success}")

        self.position = state
        self.send_state()


# FAN DEVICE
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
        action = action.upper()
        if action == "ON":
            new_state = True
        elif action == "OFF":
            new_state = False
        else:
            print(f"[{self.device_id}] Unknown action: {action}")
            return

        success = self.arduino.send_fan_command(self.pin, new_state)
        print(f"[{self.device_id}] command success = {success}")

        self.state = new_state
        self.send_state()


# MOTION SENSOR DEVICE
# class MotionSensorDevice(BaseDevice):
#     def __init__(self, device_id: str, name: str, pin: int, arduino: ArduinoSerial):
#         super().__init__(device_id, name, pin, arduino)
#         self.motion_detected = False

#     def send_register(self):
#         msg = {
#             "type": "register_device",
#             "sender_id": self.device_id,
#             "payload": {"deviceType": "motion_sensor"}
#         }
#         send_json(self.sock, msg)
#         print(f"[{self.device_id}] Registered as motion sensor device")

#     def send_ui_definition(self):
#         msg = {
#             "type": "ui_definition",
#             "sender_id": self.device_id,
#             "payload": {"ui": []}  # No UI controls for sensor
#         }
#         send_json(self.sock, msg)

#     def send_state(self):
#         msg = {
#             "type": "device_state",
#             "sender_id": self.device_id,
#             "payload": {"state": {"motionDetected": self.motion_detected}}
#         }
#         send_json(self.sock, msg)
#         print(f"[{self.device_id}] Motion: {self.motion_detected}")

#     def handle_action(self, action: str):
#         print(f"[{self.device_id}] Motion sensor does not support actions")


# SMOKE SENSOR DEVICE (MQ-2)
class SmokeSensorDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, threshold: int, arduino: ArduinoSerial):
        super().__init__(device_id, name, pin, arduino)
        self.smoke_level = 0
        self.threshold = threshold
        self.smoke_detected = False
        self.polling_thread = None

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "smoke_sensor"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as smoke sensor device")

    def send_ui_definition(self):
        msg = {
            "type": "ui_definition",
            "sender_id": self.device_id,
            "payload": {"ui": []}  # No UI controls for sensor
        }
        send_json(self.sock, msg)

    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {
                "state": {
                    "smokeLevel": self.smoke_level,
                    "smokeDetected": self.smoke_detected,
                    "threshold": self.threshold
                }
            }
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Smoke level: {self.smoke_level}, Detected: {self.smoke_detected}")

    def handle_action(self, action: str):
        print(f"[{self.device_id}] Smoke sensor does not support actions")

    def start_polling(self):
        """Start background thread to poll sensor values."""
        self.polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.polling_thread.start()

    def _poll_loop(self):
        while self.running:
            new_level = self.arduino.read_analog(self.pin)
            new_detected = new_level > self.threshold
            
            # Only send state if changed
            if new_level != self.smoke_level or new_detected != self.smoke_detected:
                self.smoke_level = new_level
                self.smoke_detected = new_detected
                self.send_state()
            
            time.sleep(2)  # Poll every 2 seconds


# TEMPERATURE SENSOR DEVICE
class TemperatureSensorDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, threshold_high: float, threshold_low: float, arduino: ArduinoSerial):
        super().__init__(device_id, name, pin, arduino)
        self.temperature = 20.0
        self.threshold_high = threshold_high
        self.threshold_low = threshold_low
        self.status = "normal"  # "normal", "hot", "cold"
        self.polling_thread = None

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "temperature_sensor"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as temperature sensor device")

    def send_ui_definition(self):
        msg = {
            "type": "ui_definition",
            "sender_id": self.device_id,
            "payload": {"ui": []}  # No UI controls for sensor
        }
        send_json(self.sock, msg)

    def send_state(self):
        msg = {
            "type": "device_state",
            "sender_id": self.device_id,
            "payload": {
                "state": {
                    "steamLevel": self.temperature,
                    "status": self.status,
                    "thresholdHigh": self.threshold_high,
                    "thresholdLow": self.threshold_low
                }
            }
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Temperature: {self.temperature}C, Status: {self.status}")

    def handle_action(self, action: str):
        print(f"[{self.device_id}] Temperature sensor does not support actions")

    def start_polling(self):
        """Start background thread to poll sensor values."""
        self.polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.polling_thread.start()

    def _poll_loop(self):
        while self.running:
            raw_value = self.arduino.read_analog(self.pin)
            # Convert raw analog value to temperature (simplified conversion)
            # Actual conversion depends on the sensor type (LM35, TMP36, etc.)
            new_temp = round((raw_value * 5.0 / 1024.0) * 100, 1)  # LM35 conversion
            
            # Determine status
            if new_temp > self.threshold_high:
                new_status = "hot"
            elif new_temp < self.threshold_low:
                new_status = "cold"
            else:
                new_status = "normal"
            
            # Only send state if changed significantly
            if abs(new_temp - self.temperature) > 0.5 or new_status != self.status:
                self.temperature = new_temp
                self.status = new_status
                self.send_state()
            
            time.sleep(5)  # Poll every 5 seconds


# ALARM DEVICE (Buzzer)
class AlarmDevice(BaseDevice):
    def __init__(self, device_id: str, name: str, pin: int, arduino: ArduinoSerial):
        super().__init__(device_id, name, pin, arduino)
        self.state = False
        self.frequency = 1000  # Default alarm frequency in Hz

    def send_register(self):
        msg = {
            "type": "register_device",
            "sender_id": self.device_id,
            "payload": {"deviceType": "alarm"}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] Registered as alarm device")

    def send_ui_definition(self):
        ui = [
            {"type": "button", "action": "ON", "label": f"{self.name} ON"},
            {"type": "button", "action": "OFF", "label": f"{self.name} OFF"},
            {"type": "button", "action": "TEST", "label": f"{self.name} TEST"},
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
            "payload": {"state": {"alarmOn": self.state, "frequency": self.frequency}}
        }
        send_json(self.sock, msg)
        print(f"[{self.device_id}] State: {'ON' if self.state else 'OFF'}")

    def handle_action(self, action: str):
        action = action.upper()
        if action == "ON":
            new_state = True
        elif action == "OFF":
            new_state = False
        elif action == "TEST":
            # Short test beep
            self.arduino.send_alarm_command(self.pin, True, 2000)
            time.sleep(0.5)
            self.arduino.send_alarm_command(self.pin, False)
            return
        else:
            print(f"[{self.device_id}] Unknown action: {action}")
            return

        success = self.arduino.send_alarm_command(self.pin, new_state, self.frequency)
        print(f"[{self.device_id}] command success = {success}")

        self.state = new_state
        self.send_state()

    def trigger_alarm(self):
        """Programmatically trigger the alarm (called by automation)."""
        self.state = True
        self.arduino.send_alarm_command(self.pin, True, self.frequency)
        self.send_state()

    def stop_alarm(self):
        """Programmatically stop the alarm."""
        self.state = False
        self.arduino.send_alarm_command(self.pin, False)
        self.send_state()


# HARDWARE BRIDGE
class HardwareBridge:
    def __init__(self, serial_port: str, simulate: bool = False):
        self.arduino = ArduinoSerial(serial_port, simulate)
        self.devices = []
        self.threads = []
        
        # Store references to special devices for automation
        self.motion_device = None
        self.smoke_device = None
        self.temp_device = None
        self.alarm_device = None
        self.led_devices = []
        self.fan_devices = []
        
        # Create LED devices
        for config in LED_DEVICES:
            device = LEDDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                arduino=self.arduino
            )
            self.devices.append(device)
            self.led_devices.append(device)

        # Create Fan devices
        for config in FAN_DEVICES:
            device = FanDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                arduino=self.arduino
            )
            self.devices.append(device)
            self.fan_devices.append(device)

        # Create Servo devices (window)
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

        # Create Door devices
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
        
        # Create Motion Sensor devices
        # for config in MOTION_SENSOR_DEVICES:
        #     device = MotionSensorDevice(
        #         device_id=config["id"],
        #         name=config["name"],
        #         pin=config["pin"],
        #         arduino=self.arduino
        #     )
        #     self.devices.append(device)
        #     self.motion_device = device

        # Create Smoke Sensor devices
        for config in SMOKE_SENSOR_DEVICES:
            device = SmokeSensorDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                threshold=config["threshold"],
                arduino=self.arduino
            )
            self.devices.append(device)
            self.smoke_device = device

        # Create Temperature Sensor devices
        for config in TEMPERATURE_SENSOR_DEVICES:
            device = TemperatureSensorDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                threshold_high=config["threshold_high"],
                threshold_low=config["threshold_low"],
                arduino=self.arduino
            )
            self.devices.append(device)
            self.temp_device = device

        # Create Alarm devices
        for config in ALARM_DEVICES:
            device = AlarmDevice(
                device_id=config["id"],
                name=config["name"],
                pin=config["pin"],
                arduino=self.arduino
            )
            self.devices.append(device)
            self.alarm_device = device

        # Set event callback for Arduino events
        self.arduino.set_event_callback(self.handle_arduino_event)

    def handle_arduino_event(self, line: str):
        """Handle events from Arduino (motion, smoke, temp alerts)."""
        if line.startswith("MOTION:"):
            if self.motion_device:
                detected = line == "MOTION:1"
                self.motion_device.motion_detected = detected
                self.motion_device.send_state()
                
                # Automation: Turn on lights when motion detected
                if detected and self.led_devices:
                    print("[Automation] Motion detected - turning on lights")
                    for led in self.led_devices:
                        if not led.state:
                            led.handle_action("ON")

        elif line.startswith("SMOKE:"):
            if self.smoke_device:
                try:
                    level = int(line.split(":")[1])
                    self.smoke_device.smoke_level = level
                    self.smoke_device.smoke_detected = level > self.smoke_device.threshold
                    self.smoke_device.send_state()
                    
                    # Automation: Trigger alarm if smoke detected
                    if self.smoke_device.smoke_detected and self.alarm_device:
                        print("[Automation] Smoke detected - triggering alarm!")
                        self.alarm_device.trigger_alarm()
                except ValueError:
                    pass

        elif line.startswith("TEMP:"):
            if self.temp_device:
                try:
                    temp = float(line.split(":")[1])
                    self.temp_device.temperature = temp
                    
                    # Update status
                    if temp > self.temp_device.threshold_high:
                        self.temp_device.status = "hot"
                        # Automation: Turn on fan when hot
                        if self.fan_devices:
                            print("[Automation] High temperature - turning on fan")
                            for fan in self.fan_devices:
                                if not fan.state:
                                    fan.handle_action("ON")
                    elif temp < self.temp_device.threshold_low:
                        self.temp_device.status = "cold"
                    else:
                        self.temp_device.status = "normal"
                    
                    self.temp_device.send_state()
                except ValueError:
                    pass
                        
    def start(self, host: str, port: int):
        print(f"\n{'='*50}")
        print("Hardware Bridge Starting")
        print(f"Server: {host}:{port}")
        print(f"Devices: {len(self.devices)}")
        print(f"{'='*50}\n")
        
        # Connect and register all devices
        for device in self.devices:
            device.connect(host, port)
            device.send_register()
            device.send_ui_definition()
            device.send_state()

        # Start Arduino reader for events
        # self.arduino.start_reader()
        
        # Start device run loops
        for device in self.devices:
            thread = threading.Thread(target=device.run, daemon=True)
            thread.start()
            self.threads.append(thread)
        
        # Start sensor polling threads
        if self.smoke_device:
            self.smoke_device.start_polling()
        if self.temp_device:
            self.temp_device.start_polling()
        
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
    parser = argparse.ArgumentParser(description="Hardware Bridge for Arduino Smart Home")
    parser.add_argument("--simulate", action="store_true", 
                        help="Run without Arduino (simulation mode)")
    parser.add_argument("--port", default=DEFAULT_SERIAL_PORT,
                        help=f"Serial port for Arduino (default: {DEFAULT_SERIAL_PORT})")
    parser.add_argument("--server", default=SERVER_HOST,
                        help=f"Server hostname (default: {SERVER_HOST})")
    parser.add_argument("--server-port", type=int, default=SERVER_PORT,
                        help=f"Server port (default: {SERVER_PORT})")
    
    args = parser.parse_args()
    
    bridge = HardwareBridge(args.port, args.simulate)
    bridge.start(args.server, args.server_port)


if __name__ == "__main__":
    main()