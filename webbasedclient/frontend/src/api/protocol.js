// (matches python server)

export const ENVELOPE_KEYS = {
  TYPE: "type",
  SENDER_ID: "sender_id",
  PAYLOAD: "payload",
};

export const MSG = {
  LOGIN: "login",
  LOGIN_OK: "login_ok",
  LOGIN_FAILED: "login_failed",

  GET_DEVICES: "get_devices",
  DEVICE_LIST: "device_list",

  GET_UI: "get_ui",
  UI_DEFINITION: "ui_definition",

  ACTION: "action",
  STATE_UPDATE: "state_update",

  ERROR: "error",
};

// Message builders
export function buildLogin(sender_id, email, password) {
  return {
    type: MSG.LOGIN,
    sender_id,
    payload: { email, password },
  };
}

export function buildGetDevices(sender_id) {
  return {
    type: MSG.GET_DEVICES,
    sender_id,
    payload: {},
  };
}

export function buildGetUi(sender_id, deviceId) {
  return {
    type: MSG.GET_UI,
    sender_id,
    payload: { deviceId },
  };
}

export function buildAction(sender_id, deviceId, action) {
  return {
    type: MSG.ACTION,
    sender_id,
    payload: { deviceId, action },
  };
}