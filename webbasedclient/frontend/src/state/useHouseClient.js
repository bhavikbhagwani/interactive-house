// React hook that mirrors the unit_client.py logic:
// login -> get_devices -> get_ui -> action -> state_update

import { useEffect, useMemo, useRef, useState } from "react";
import { WsClient } from "../api/wsClient";
import { MSG, buildAction, buildGetDevices, buildGetUi, buildLogin } from "../api/protocol";

// the routing states
export const VIEW = {
  LOGIN: "login",
  DEVICES: "devices",
  DEVICE: "device",
};

export function useHouseClient(options = {}) {
  const senderId = options.senderId || "web-1";

  
  const wsUrl =
    options.wsUrl ||
    (import.meta?.env?.VITE_WS_URL ?? "ws://localhost:3001");

  const [connected, setConnected] = useState(false);
  const [view, setView] = useState(VIEW.LOGIN);

  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);

  const [uiItems, setUiItems] = useState([]);
  const [latestState, setLatestState] = useState({});

  const [statusMsg, setStatusMsg] = useState("");

  const [actionPending, setActionPending] = useState(false);

  const wsRef = useRef(null);

  const handleMessage = (msg) => {
    const type = msg?.type;
    const payload = msg?.payload || {};

    console.log("RECV:", type, msg);

    switch (type) {
      case MSG.LOGIN_OK: {
        setStatusMsg("Login OK");
        setView(VIEW.DEVICES);
        // after login, request device list
        wsRef.current?.send(buildGetDevices(senderId));
        return;
      }

      case MSG.LOGIN_FAILED: {
        setStatusMsg("Login failed");
        setView(VIEW.LOGIN);
        return;
      }

      case MSG.DEVICE_LIST: {
        const list = payload.devices || [];
        setDevices(list);
        setStatusMsg(`Received ${list.length} devices`);
        return;
      }

      case MSG.UI_DEFINITION: {
        const deviceId = payload.deviceId;
        const ui = payload.ui || [];
        const state = payload.state || {};

        setSelectedDeviceId(deviceId);
        setUiItems(ui);
        setLatestState(state);
        setView(VIEW.DEVICE);
        setStatusMsg(`Loaded UI for ${deviceId}`);
        return;
      }

      case MSG.STATE_UPDATE: {

        const deviceId = payload.deviceId;
        const state = payload.state || {};

        // only apply updates for the currently open device
        if (selectedDeviceId && deviceId && deviceId !== selectedDeviceId) return;

        setLatestState((prev) => ({ ...prev, ...state }));
        setActionPending(false);
        setStatusMsg(`State update for ${deviceId || "device"}`);
        return;
      }

      case MSG.ERROR: {
        setActionPending(false);
        setStatusMsg(`Error: ${payload.message || "Unknown error"}`);
        return;
      }

      default: {
        // Ignore unknown messages for now
        return;
      }
    }
  };

  const client = useMemo(() => {
    return new WsClient({
      onMessage: handleMessage,
      onStatus: (s) => setConnected(Boolean(s.connected)),
    });
  }, []);

  useEffect(() => {
    wsRef.current = client;
    client.connect(wsUrl);

    return () => {
      client.disconnect();
    };
  }, [client, wsUrl]);

  // Actions (similar to send_json(...) in the CLI)
  const login = (email, password) => {
    setStatusMsg("Logging in...");
    wsRef.current?.send(buildLogin(senderId, email, password));
  };

  const refreshDevices = () => {
    setStatusMsg("Fetching devices...");
    wsRef.current?.send(buildGetDevices(senderId));
  };

  const openDevice = (deviceId) => {
    setStatusMsg(`Fetching UI for ${deviceId}...`);
    wsRef.current?.send(buildGetUi(senderId, deviceId));
  };

  const backToDevices = () => {
    setView(VIEW.DEVICES);
    setSelectedDeviceId(null);
    setUiItems([]);
    setLatestState({});
    refreshDevices();
  };

  const sendAction = (action) => {
  if (!selectedDeviceId || actionPending) return;
    setActionPending(true);
    setStatusMsg(`Sending action ${action}...`);
    wsRef.current?.send(buildAction(senderId, selectedDeviceId, action));
  };

  return {
    // connection + "routing"
    connected,
    view,
    statusMsg,

    // data
    devices,
    selectedDeviceId,
    uiItems,
    latestState,

    actionPending,

    // actions
    login,
    refreshDevices,
    openDevice,
    backToDevices,
    sendAction,
  };
}