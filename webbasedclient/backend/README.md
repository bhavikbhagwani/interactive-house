# Mustafa — Step-by-step (Web Unit Team)

## Step 1 — Confirm endpoints (5 min)
- Python server TCP: `localhost:5001`
- Decide gateway WS URL for browser: e.g. `ws://localhost:8080`
- Write these in `.env` placeholders (even if not implemented yet)

## Step 2 — Build the Node Gateway (minimum viable)
- Create `Webbasedclient/gateway/`
- Gateway must do only:
  1) Accept WebSocket clients (browser)
  2) Open TCP connection to Python server
  3) Forward messages:
     - WS JSON → TCP NDJSON (JSON + `\n`)
     - TCP NDJSON → WS JSON

## Step 3 — Add lifecycle handling
- If WS client disconnects → close its TCP connection
- If TCP disconnects/errors → notify WS client + close WS cleanly
- Log: WS connected/disconnected, TCP connected/disconnected

## Step 4 — Wire React to the gateway
- Use the existing `WsClient`
- On app start:
  - `ws.connect(WS_URL)`
- Show connection status (connected / disconnected)

## Step 5 — Implement message flow in React (in this order)
1) **Login**
   - Send `login`
   - Handle `login_ok` / `login_failed`
2) **Device list**
   - Send `get_devices`
   - Render `device_list.payload.devices`
3) **Device UI**
   - On selecting device: send `get_ui` with `deviceId`
   - Render dynamic UI from `ui_definition.payload.ui`
   - Initialize displayed state from `ui_definition.payload.state`
4) **Actions**
   - On button click: send `action` with `deviceId` + `action`
5) **Live updates**
   - On `state_update`: update local state store

## Step 6 — Error handling (must-have)
- On `error` message: show banner/toast text
- Don’t crash the app

## Step 7 — Smoke test checklist (what “done” means)
- Start Python server + devices
- Start gateway
- Start React
- Verify:
  - login works
  - device list loads
  - UI loads per device
  - actions trigger device behavior
  - state updates arrive live
  - unknown deviceId → error shown
  - action to disconnected device → error shown

## Step 8 — Write your short README section (copy/paste)
- “How to run gateway”
- “How to run frontend”
- “Expected WS_URL + TCP host/port”
- “Known message types we handle”