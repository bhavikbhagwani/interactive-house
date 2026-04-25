# Iterations 4 & 5 — Final development phase

Iterations 4 and 5 are merged into one final development phase. The purpose of this phase is to complete the Interactive House system by strengthening authorization, expanding the physical house with more sensors, introducing assistive automation, improving accessibility, and making the user interfaces more polished and consistent across platforms.

## Section 1: Final scope

Just these six things:

1. RBAC
2. More sensors
3. Automation
4. Unified UI
5. Scenes
6. Speech-to-text

---

## Section 2: Technical approach

### 1. Simple RBAC

**What we already have**

In the server:

- `users` table already has `role`
- `verify_login()` returns the role
- `login_ok` already sends the role back to the client

So authentication already exists. We only need to add authorization enforcement.

**Main idea**

- When a user logs in:
  - the server knows their `userId`
  - the server knows their `role`
- When the user requests something:
  - server checks if that role is allowed to access that device

**What to add**

We should add a small in-memory user session structure on the server, something like:

```python
authenticated_users = {}
```

Where:

- **key** = socket
- **value** = `{userId, email, role}`

Then when `handle_login_for_gui()` succeeds, we save the logged-in user there.

That way, later in:

- `handle_get_devices()`
- `handle_get_ui()`
- `handle_action()`

we can easily check the role.

**Permission model**

We also need a permission model, using **device-level authorization**, so authorize based on **device type**, not individual device IDs.

For example:

- `primary_user` can access all device types / everything
- `caregiver` can access: `led`, `fan`, `sensors`
- `caregiver` cannot access: `door`, `Window`, or any other devices

We could do it like this:

```python
ROLE_ALLOWED_DEVICE_TYPES = {
    "primary_user": {"led", "door", "servo", "fan", "sensor"},
    "caregiver": {"led", "fan", "sensor"},
}
```

**Where RBAC must be enforced**

RBAC should not only happen in `handle_action()`. It should happen in three places:

- `handle_get_devices(sock)` — Only send devices that the logged-in role is allowed to see.
- `handle_get_ui(sock, unit_id, payload)` — If the user requests a forbidden device, return error.
- `handle_action(sock, unit_id, payload)` — Final check before forwarding action to device.

That way:

- unauthorized devices do not show up
- unauthorized UIs cannot be opened
- unauthorized actions are still blocked even if a client tries manually

That is the cleanest and strongest implementation.

**Seeded users**

Our demo users currently have role `"user"`. We must change this.

For final demo, seed at least:

- one `primary_user`
- one `caregiver`

For example:

- `primary@email.com` / `primary123` / `primary_user`
- `caregiver@email.com` / `caregiver123` / `caregiver`

---

### 2. Expanded physical house integration

This is mainly device-side work.

**Current hardware-supported devices**

- `led-1`, `led-2`
- `fan-1`
- `servo-1` (window)
- `door-1`

**Missing for final iteration**

We want:

- motion sensor
- smoke sensor
- temperature sensor

and possibly also:

- alarm / buzzer device

**How these should fit the current bridge architecture**

Our bridge already treats each physical component as a separate logical device class:

- `LEDDevice`, `FanDevice`, `ServoDevice`, `DoorDevice`

We continue the same pattern and add:

- `MotionSensorDevice`
- `SmokeSensorDevice`
- `TemperatureSensorDevice`
- maybe `AlarmDevice`

**Sensor behavior**

These sensor devices are different from actuators (devices like LED or fan). They should:

- register with the server
- send UI definition
- send initial state
- periodically or eventfully send state updates

They do not need normal action buttons if they are read-only.

So their device class will probably:

- still implement `send_register()`
- still implement `send_ui_definition()`
- still implement `send_state()`
- but `handle_action()` may be empty or unused

**Possible sensor state examples**

- `{"motionDetected": true}`
- `{"smokeDetected": false}`
- `{"temperature": 24.5}`

**UI definition for sensors**

Our unit clients currently only render button items. That means a pure sensor UI cannot rely on controls. But that is okay because the device page shows human-readable state. So even if a sensor UI is just `{"ui": []}`, the sensor can still work, because the current state will still be displayed.

**Main technical risk:** sensor integration may require changes both in Arduino firmware and in the Python bridge, since the current bridge is mainly designed around command/response communication for actuators.

---

### 3. Event-driven assistive automation

This is one of the strongest final features, and it belongs on the **server** because:

- the server already receives all state updates
- the server already routes actions
- the server is central and authoritative
- automation should not depend on whether web or Android is open

So the automation logic should not be in the clients and should not be in the Arduino bridge.

**Where to put this automation**

The best place is inside `handle_device_state(device_id, payload)`.

Right now it:

- updates in-memory state
- saves to DB
- broadcasts to units

After iteration 4+5 it should also:

- check whether the new state triggers an automation rule
- if yes, send action(s) to device(s)

We do not write all automation directly inline in `handle_device_state()`. Instead, add a helper such as:

- `run_automation_rules(device_id, state)`

**Our automation rules**

- motion detected → lights ON
- no motion → lights OFF
- smoke detected → alarm ON
- high temperature → fan ON

Right now, there is no alarm / buzzer device in the hardware bridge. We will add this only if the Arduino house supports it.

**Note:** Automation is triggered whenever a device sends a new state update to the server.

---

### 4. Unified client design

This is mainly client-side work, affecting both the web client and the Android client, with minimal server-side impact.

We use the **Android** client design as the reference and make the **web** client match it as closely as practical. It does not have to be pixel-perfect, just structurally consistent. That is preferable to changing both clients. The Android UI is strong, so we replicate that look and structure into the web client UI.

**Another change in the web client**

Our device interpretation logic is based on `deviceId` prefixes:

- `deviceId.startsWith("led")`
- `deviceId.startsWith("door")`
- `deviceId.startsWith("fan")`
- etc.

By adding more devices:

- motion sensor, smoke sensor, temp sensor, alarm, scenes

we will need to extend these helpers:

- `getReadableState()` in `DevicePage`
- `getDeviceTitle()` in `DevicePage`
- maybe the device list labels in `DeviceListPage`

---

### 5. Scenes

A **scene** is:

- one user intent
- multiple device actions

Example: **“good night”** — lights OFF, door CLOSE, fan OFF. (This kind of multi-action “scene” was suggested as a good fit after the guest lecture.)

Clients (web and Android) will send something like this to the server:

```json
{
  "type": "trigger_scene",
  "sender_id": "web-1",
  "payload": { "sceneId": "good_night" }
}
```

Then the server:

- checks login
- checks role authorization
- looks up scene actions
- sends the relevant actions to devices

**Scene definitions**

These can be hardcoded in the server for now. For example:

- **good_night:** `led-1` OFF, `led-2` OFF, `door-1` CLOSE, `fan-1` OFF
- **good_morning:** `led-1` ON, `led-2` ON, `door-1` OPEN, `fan-1` ON

**Where to show scenes in clients**

Show scene buttons on the **device list page** (e.g. two buttons: Good Morning and Good Night).

---

### 6. Speech to text

This should be split into two parts:

- **Part 1 — speech recognition:** on Android, using Android’s built-in speech-to-text.
- **Part 2 — command interpretation:** on the server.

**Android side**

User taps microphone button. Speech becomes text, for example:

- “turn on led one”
- “turn off fan”
- “good night”
- “good morning”

Then Android sends a message like:

```json
{
  "type": "voice_command",
  "sender_id": "android-1",
  "payload": { "text": "good night" }
}
```

**Server side**

The server:

- checks login
- interprets command text
- maps it either to a normal action or a scene
- checks authorization
- executes it

That is the best architecture.

**Keep voice scope very small**

Only support a known list of commands, for example:

- “turn on led one”
- “turn off led one”
- “turn on fan”
- “turn off fan”
- “open door”
- “close door”
- “good night”
- “good morning”

That is enough for a strong accessibility demo.

---

## Summarized subgroup responsibilities

**Server team**

- Implement RBAC
- Filter device visibility and device access by role
- Add scene handling
- Add voice command handling
- Add server-side automation rules based on sensor updates

**Device / IoT team**

- Add motion, smoke, and temperature sensor support
- Update the Arduino firmware
- Update the Python hardware bridge
- Add alarm/buzzer support if possible
- Make sure sensor values are sent correctly to the server

**Web client team**

- Support the new sensor and alarm devices in the UI
- Add scene buttons: Good Morning and Good Night
- Handle authorization errors or any errors cleanly
- Update the design to match the final Android UI

**Android client team**

- Support the new sensor and alarm devices in the UI
- Add scene buttons: Good Morning and Good Night
- Implement speech-to-text
- Send voice commands to the server
- Handle authorization errors or any errors cleanly
