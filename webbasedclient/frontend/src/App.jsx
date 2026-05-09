import { useHouseClient, VIEW } from "./state/useHouseClient";

import LoginPage from "./pages/LoginPage";
import DeviceListPage from "./pages/DeviceListPage";
import DevicePage from "./pages/DevicePage";

export default function App() {
  const hc = useHouseClient();

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
        deviceStates={hc.deviceStates}
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
      actionPending={hc.actionPending}
      onBack={hc.backToDevices}
      onAction={hc.sendAction}
    />
  );
}