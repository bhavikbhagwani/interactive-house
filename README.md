# Interactive House Project

The goal is to design a server-centric, distributed system that allows users—especially people with functional disabilities—to independently control their home environment in a simple, accessible, and secure way.

The system supports permission-based control, where different users (e.g. user vs caregiver) may have different access rights. Devices provide their own UI definitions, and users interact through mobile or web-based units.

## Architecture

All communication goes through a central server:

- No direct unit ↔ device communication

- Devices register dynamically and upload their UI

- Units render device-provided UIs without hardcoding device logic

## Development Approach

The project follows an iterative (RUP-inspired) process.
Each iteration delivers a working system, even if small, and builds on the previous one.

## Iteration 1 – Overview

Goal: prove the end-to-end architecture works.

Scope:

- One Python TCP server

- One simulated device (light)

- One Python unit (CLI client)

Focus:

- Device registration

- Dynamic UI distribution

- User actions and state updates

- In-memory state only (no DB, no permissions, no Android app yet)

## Iteration 2 – Overview

Goal: scale the working end-to-end architecture from Iteration 1 by adding persistence, more devices, and real clients.

Scope:

- Server upgraded with SQLite persistence (devices, UI definitions, last known state, seeded users)

- Multiple simulated devices

- Android unit client (Kotlin) replacing the Python CLI as the primary unit

- Web-based unit client

Focus:

- Persistence across server restarts (server reloads devices/UI/state from SQLite on startup)

- Same NDJSON message protocol across Android and Web

- Device-provided UI rendered dynamically across platforms

Not in scope yet:

- Role-based access control (RBAC) / permissions (planned for Iteration 3)

- Advanced security (encryption, password hashing, signup/account management)

### Run the web based client (React + Node Gateway) (Windows)

#### start the python server

```bash
    cd server
    pip install -r requirements.txt
    python server.py
```
Demo login credentials (seeded):

user@email.com / user123

bhavik@email.com / bhavik

meryam@email.com / meryam

Note: This is login only (no sign-up in Iteration 2). Users are seeded into SQLite on server startup.

#### start the simulated devices

```bash
    cd device
    python light.py
    python door.py
    python coffee_machine.py
```
#### Start the Node WebSocket Gateway (Browser ↔ TCP Bridge)

```bash
    cd webbasedclient/backend/gateway
    npm install
    npm start
```


#### Start the React Frontend

```bash
    cd webbasedclient/frontend
    npm install
    npm run dev
```

#### Test flow (Web UI)

- Verify Connected: Yes

- Login with one of the demo users

- Refresh device list

- Open a device → UI is rendered dynamically from the device-provided UI definition

- Press buttons → actions go Unit → Server → Device, and state updates are broadcast back

### Run the Android Client (Android Studio + Emulator) (Windows)

#### start the python server

```bash
    cd server
    pip install -r requirements.txt
    python server.py
```
Demo login credentials (seeded):

user@email.com / user123

bhavik@email.com / bhavik

meryam@email.com / meryam

Note: This is login only (no sign-up in Iteration 2). Users are seeded into SQLite on server startup.

#### start the simulated devices

```bash
    cd device
    python light.py
    python door.py
    python coffee_machine.py
```
#### Open the Android project in Android Studio and run the app

#### Test flow (Android app)

- Login with one of the demo users

- The device list will load from the server

- Select a device (Light / Door / Coffee Machine)

- Press buttons → actions go Unit → Server → Device, and state updates are broadcast back

## Iteration 3 – Overview

Goal: integrate the physical Arduino house into the system and validate that the architecture works with real hardware devices.

Scope:

- Existing Python TCP server (architecture unchanged)

- Physical Arduino devices (LED lights and window)

- Python hardware bridge connecting the Arduino to the server

- Existing unit clients (Web and Android)

Focus:

- Replacing simulated light devices with physical Arduino-controlled lights

- End-to-end interaction from unit client → server → physical device

- Maintaining the same device registration, UI definition, and state update flow

- UI improvements for the Web and Android clients

Not in scope:

- Role-based access control (RBAC) / permissions (planned for Iteration 4)

- Advanced security (encryption, authentication improvements)

- Full physical implementation of all house devices (only lights and window for now)

### Run the web based client (React + Node Gateway) (Windows)

#### start the python server

```bash
    cd server
    pip install -r requirements.txt
    python server.py
```
Demo login credentials (seeded):

user@email.com / user123

Note: This is login only (no sign-up). Users are seeded into SQLite on server startup.

#### option A: Run with simulated hardware bridge (no Arduino required)

This mode simulates the physical house but still uses the hardware bridge architecture.

```bash
    cd device
    python hardw_bridge.py --simulate
```

#### option B: Run with real Arduino hardware

- Upload Arduino firmware
- Open main.cpp in Arduino IDE
- Select board: Arduino UNO
- Select correct port (e.g. COM7)
- Upload the firmware to the board
- Connect Arduino via USB
- Start hardware bridge (real mode):

```bash
    cd device
    python hardw_bridge.py --port COM7
```

#### Start the Node WebSocket Gateway (Browser ↔ TCP Bridge)

```bash
    cd webbasedclient/backend/gateway
    npm install
    npm start
```

#### Start the React Frontend

```bash
    cd webbasedclient/frontend
    npm install
    npm run dev
```

#### Test flow (Web UI)

- Verify Connected: Yes
- Login with one of the demo users
- Refresh device list

You should see devices such as:

- LED 1
- LED 2
- Fan
- Window (servo)
- Door

#### Interaction

- Open a device → UI is rendered dynamically (device-provided UI)

- Press buttons → actions flow:
```bash
Web UI → Gateway → Server → Hardware Bridge → Arduino → Physical Device
```

Device state updates are sent back:

```bash
Arduino → Hardware Bridge → Server → Web UI
```

#### Expected behavior

- LED turns ON/OFF physically

- Fan activates/deactivates

- Door/servo responds (if connected)

- UI updates after action (with slight delay due to hardware communication)

### Run the Android Client (Android Studio + Emulator) (Windows)

to be defined later