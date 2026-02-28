import { useHouseClient, VIEW } from "./state/useHouseClient";

import LoginPage from "./pages/LoginPage";
import DeviceListPage from "./pages/DeviceListPage";
import DevicePage from "./pages/DevicePage";

const MOCK = true;

export default function App() {
   const hc = MOCK
    ? {
        view: VIEW.LOGIN, // change between VIEW.LOGIN / VIEW.DEVICES / VIEW.DEVICE to see if it works.
        connected: true,
        statusMsg: "mock: ok",
        login: (u, p) => console.log("login", u, p),

        devices: [
          { deviceId: "light-1", deviceType: "light" },
          { deviceId: "door-1", deviceType: "door_lock" },
          
        ],
        refreshDevices: () => console.log("refresh devices"),
        openDevice: (id) => console.log("open device", id),

        selectedDeviceId: "light-1",
        uiItems: [
          { type: "button", label: "Turn ON", action: "ON" },
          { type: "button", label: "Turn OFF", action: "OFF" },
        ],
        latestState: { lightOn: false },

        backToDevices: () => console.log("back"),
        sendAction: (a) => console.log("action", a),
      }
    : useHouseClient();

  if (hc.view === VIEW.LOGIN) {
    return (
      <LoginPage
        connected={hc.connected}
        statusMsg={hc.statusMsg}
        onLogin={hc.login}
      />
    );
  }

  if (hc.view === VIEW.DEVICES) {
    return (
      <DeviceListPage
        devices={hc.devices}
        statusMsg={hc.statusMsg}
        onRefresh={hc.refreshDevices}
        onOpenDevice={hc.openDevice}
      />
    );
  }

  // VIEW.DEVICE
  return (
    <DevicePage
      deviceId={hc.selectedDeviceId}
      uiItems={hc.uiItems}
      state={hc.latestState}
      statusMsg={hc.statusMsg}
      onBack={hc.backToDevices}
      onAction={hc.sendAction}
    />
  );
}