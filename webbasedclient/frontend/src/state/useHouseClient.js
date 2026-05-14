// React hook that mirrors the unit_client.py logic:
// login -> get_devices -> get_ui -> action -> state_update

import { useCallback, useEffect, useRef, useState } from "react";
import { WsClient } from "../api/wsClient";
import {
  MSG,
  buildAction,
  buildGetDevices,
  buildGetUi,
  buildLogin,
  buildTriggerScene,
} from "../api/protocol";

export const VIEW = {
  LOGIN: "login",
  DEVICES: "devices",
  DEVICE: "device",
};

export function useHouseClient(options = {}) {
  const senderId = options.senderId || "web-1";

  const wsUrl =
    options.wsUrl || (import.meta?.env?.VITE_WS_URL ?? "ws://localhost:3001");

  const [connected, setConnected] = useState(false);
  const [view, setView] = useState(VIEW.LOGIN);

  const [devices, setDevices] = useState([]);
  const [deviceStates, setDeviceStates] = useState({});

  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [uiItems, setUiItems] = useState([]);
  const [latestState, setLatestState] = useState({});

  const [statusMsg, setStatusMsg] = useState("");
  const [actionPending, setActionPending] = useState(false);

  const [scenePending, setScenePending] = useState(false);

  const [role, setRole] = useState(null);

  const wsRef = useRef(null);
  const selectedDeviceIdRef = useRef(null);

  useEffect(() => {
    selectedDeviceIdRef.current = selectedDeviceId;
  }, [selectedDeviceId]);

  const handleMessage = useCallback(
    (msg) => {
      const type = msg?.type;
      const payload = msg?.payload || {};

      console.log("RECV:", type, msg);

      switch (type) {
        case MSG.LOGIN_OK: {
          setStatusMsg("Login OK");
          setView(VIEW.DEVICES);
          wsRef.current?.send(buildGetDevices(senderId));
          setRole(payload.role || null);
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

          const states = {};
          for (const d of list) {
            if (d.deviceId && d.state) {
              states[d.deviceId] = d.state;
            }
          }

          setDeviceStates((prev) => ({
            ...prev,
            ...states,
          }));

          setStatusMsg(`Received ${list.length} devices`);
          return;
        }

        case MSG.UI_DEFINITION: {
          const deviceId = payload.deviceId;
          const ui = payload.ui || [];
          const state = payload.state || {};

          if (deviceId) {
            setDeviceStates((prev) => ({
              ...prev,
              [deviceId]: {
                ...(prev[deviceId] || {}),
                ...state,
              },
            }));
          }

          setSelectedDeviceId(deviceId);
          setUiItems(ui);
          setLatestState(state);
          setView(VIEW.DEVICE);
          setStatusMsg(`Loaded UI for ${deviceId}`);
          return;
        }

        case MSG.SCENE_TRIGGERED: {
          setScenePending(false);
          setActionPending(false);
          setStatusMsg(payload.message || `Scene triggered: ${payload.sceneId}`);
          return;
        }

        case MSG.STATE_UPDATE: {
          const deviceId = payload.deviceId;
          const state = payload.state || {};

          if (deviceId) {
            setDeviceStates((prev) => ({
              ...prev,
              [deviceId]: {
                ...(prev[deviceId] || {}),
                ...state,
              },
            }));
          }

          if (
            !selectedDeviceIdRef.current ||
            deviceId === selectedDeviceIdRef.current
          ) {
            setLatestState((prev) => ({ ...prev, ...state }));
            setActionPending(false);
          }

          setStatusMsg(`State update for ${deviceId || "device"}`);
          return;
        }

        case MSG.ERROR: {
          setActionPending(false);
          setScenePending(false);
          setStatusMsg(`Error: ${payload.message || "Unknown error"}`);
          return;
        }

        default: {
          return;
        }
      }
    },
    [senderId]
  );

  useEffect(() => {
    const client = new WsClient({
      onMessage: handleMessage,
      onStatus: (s) => setConnected(Boolean(s.connected)),
    });

    wsRef.current = client;
    client.connect(wsUrl);

    return () => {
      client.disconnect();
      if (wsRef.current === client) {
        wsRef.current = null;
      }
    };
  }, [handleMessage, wsUrl]);

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

  const sendScene = (sceneId) => {
    if (!sceneId) return;

    setScenePending(true);
    setStatusMsg(`Triggering scene ${sceneId}...`);
    wsRef.current?.send(buildTriggerScene(senderId, sceneId));
  };

  return {
    connected,
    view,
    statusMsg,

    devices,
    deviceStates,
    selectedDeviceId,
    uiItems,
    latestState,

    actionPending,
    scenePending,
    login,
    refreshDevices,
    openDevice,
    backToDevices,
    sendAction,
    sendScene,
    role
  };
}