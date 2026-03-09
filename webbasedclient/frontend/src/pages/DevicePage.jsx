function getReadableState(deviceId, state) {
  if (!state) return "Unknown";

  if (deviceId?.startsWith("light")) {
    return state.lightOn ? "Light is ON" : "Light is OFF";
  }

  if (deviceId?.startsWith("door")) {
    return state.locked ? "Door is LOCKED" : "Door is UNLOCKED";
  }

  if (deviceId?.startsWith("coffee")) {
    return state.isMaking ? "Coffee machine is MAKING coffee" : "Coffee machine is READY";
  }

  return JSON.stringify(state);
}

export default function DevicePage({
    deviceId, 
    uiItems,
    state, 
    statusMsg,
    onBack,
    onAction,

}) {

    return (
         <div className="center">
      <div className="box">
        <h2>Device: {deviceId}</h2>
        
        <div style={{ marginBottom: 12 }}>
              <button onClick={onBack}>Back</button>
        </div>
          
          <h3>Controls</h3>

          <div>
            {uiItems && uiItems.length > 0 ? (
                uiItems.map((item, idx) => {
                    if (item.type === "button") {

                    const isEnabled = item.enabled !== false; // default true if missing

                    return (
                        <button
                        key={idx}
                        style={{ marginRight: 8, marginBottom: 8 }}
                        onClick={() => onAction(item.action)}
                        disabled={!isEnabled}
                        title={!isEnabled ? "Device is busy" : undefined}
                        >
                        {item.label}
                        </button>
                    );
                    }

                    return null;
                })
                ) : (
                <div>No UI items</div>
                )}
          </div>
          <div style={{ marginBottom: 10, fontWeight: "bold", color: "black" }}>
            {getReadableState(deviceId, state)}
            </div>
          <h3>State</h3>
            <pre
                style={{
                    background: "#f4f4f4",
                    padding: 10,
                    color: "black",
                    borderRadius: 6,
                    border: "1px solid #ddd"
                }}
                >
                {JSON.stringify(state, null, 2)}
                </pre>

          <div style={{ marginTop: 12, color: "gray" }}>
            Status: {statusMsg}
          </div>
        </div>
    </div>

    );
}