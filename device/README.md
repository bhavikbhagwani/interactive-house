# Hardware Bridge – Arduino Smart House Integration

The Hardware Bridge connects the physical Arduino devices in the smart house to the software system through a serial port connection.
It acts as an intermediary that translates commands from the server into hardware actions such as controlling LEDs or operating a servo motor.

## Architecture

The system operates using a simple communication chain:

Server → Hardware Bridge → Arduino UNO→ Physical Devices

The hardware bridge listens for actions from the server (unit_client2 if in testing environment) and translates them into commands sent through the Arduino serial connection.

## Prerequisites

Before running the hardware bridge, ensure the following are available:

- Python installed

- Arduino IDE installed

- Arduino UNO connected to the computer via USB

- Arduino firmware uploaded to the board

- Required Python libraries installed


## Arduino Firmware

The Arduino firmware is located in the `firmware/` folder. It handles serial communication and controls all physical devices.

### Pin Configuration

| Component | Pin | Type |
|-----------|-----|------|
| LED 1 (White) | D13 | Digital Output |
| LED 2 (Yellow) | D5 | Digital Output (PWM) |
| Fan Motor INA | D7 | Digital Output |
| Fan Motor INB | D6 | Digital Output |
| Door Servo | D9 | Servo |
| Window Servo | D10 | Servo |
| Motion Sensor (PIR) | D2 | Digital Input |
| Smoke Sensor (MQ-2) | A0 | Analog Input |
| Temperature Sensor | A3 | Analog Input |
| Alarm Buzzer | D3 | Digital Output (PWM) |

### Serial Commands

The firmware accepts the following commands via Serial (9600 baud):

| Command | Description | Example |
|---------|-------------|---------|
| `LED:pin:ON` | Turn LED on | `LED:5:ON` |
| `LED:pin:OFF` | Turn LED off | `LED:5:OFF` |
| `LED:pin:PWM:value` | Set LED brightness (0-255) | `LED:5:PWM:128` |
| `FAN:ON` | Start fan | `FAN:ON` |
| `FAN:OFF` | Stop fan | `FAN:OFF` |
| `FAN:SPEED:value` | Set fan speed (0-255) | `FAN:SPEED:200` |
| `DOOR:pin:OPEN` | Open door/window | `DOOR:9:OPEN` |
| `DOOR:pin:CLOSE` | Close door/window | `DOOR:9:CLOSE` |
| `SERVO:pin:angle` | Set servo angle (0-180) | `SERVO:9:90` |
| `ALARM:pin:ON:freq` | Turn alarm on with frequency | `ALARM:3:ON:1000` |
| `ALARM:pin:OFF` | Turn alarm off | `ALARM:3:OFF` |
| `ALARM:pin:TEST` | Test alarm (short beep) | `ALARM:3:TEST` |
| `READ_ANALOG:pin` | Read analog sensor | `READ_ANALOG:0` |
| `READ_DIGITAL:pin` | Read digital sensor | `READ_DIGITAL:2` |
| `PING` | Test connection | `PING` |

### Uploading Firmware

1. Open `firmware/smart_home.ino` in Arduino IDE
2. Select **Tools > Board > Arduino Uno**
3. Select **Tools > Port > COM5** (or your COM port)
4. Click **Upload**

## Serial Port Configuration (Important)

The Arduino communicates with the computer through a serial COM port.
Each computer assigns a different COM port when the Arduino is connected.

Because of this, the correct COM port must be specified when starting the Hardware Bridge.

## Installing the Serial Driver (If Needed)

Some computers may not detect the Arduino correctly.
In that case install:

- [CP210x Universal Windows Driver](https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-drivers?tab=downloads)

After installing the driver and reconnecting the Arduino, the correct COM port should appear.

## How to Find the Arduino COM Port

1.Connect the Arduino via USB

2.Open Device Manager

3.Expand Ports (COM & LPT)

4.Locate the Arduino device (ex: Silicon Labs CP210x USB to UART Bridge)

## Running the Full System 
#### start the python server

```bash
    cd server
    python server.py
```

#### start the Hardware Bridge

Use when Arduino is connected, change according to your own COM port (ex: COM5) or use the Stimulated devices
```bash
    DEFAULT_SERIAL_PORT = "****"
```
then run 

```bash
    cd device
    python hardw_bridge.py
```
#### Start the Test Client

Run the test client to send commands to the system.

```bash
    cd unit
    python unit_client2.py
```
Now you can test the devices through the command line menu and observe the behavior of the Arduino hardware.


## Troubleshooting 

#### Arduino not connecting 

Possible causes: 
- Incorrect COM port
- Arduino not connected
- Missing driver

Solutions: 
- Check device manager for the correct COM port
- Install the CP210x Universal Windows Driver
- Restart the hardware bridge

#### Hardware not responding 

Verify that:
- The server is running

- The Arduino firmware is uploaded
