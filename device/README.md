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
