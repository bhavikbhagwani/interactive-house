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

### Run the web based client (React + Node Gateway)

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


## Iteration 3 – Overview

To be defined later