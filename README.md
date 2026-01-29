# Interactive House Project

The goal is to design a server-centric, distributed system that allows users—especially people with functional disabilities—to independently control their home environment in a simple, accessible, and secure way.

The system supports permission-based control, where different users (e.g. user vs caregiver) may have different access rights. Devices provide their own UI definitions, and users interact through mobile or web-based units.

### Architecture

All communication goes through a central server:

- No direct unit ↔ device communication

- Devices register dynamically and upload their UI

- Units render device-provided UIs without hardcoding device logic

### Development Approach

The project follows an iterative (RUP-inspired) process.
Each iteration delivers a working system, even if small, and builds on the previous one.

### Iteration 1 – Overview

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

### Iteration 2 – Overview

To be defined later