function getReadableState(deviceId, state) {
  if (!state) return "Unknown";

  if (deviceId?.startsWith("light")) {
    return state.lightOn ? "Light is ON" : "Light is OFF";
  }

  if (deviceId?.startsWith("led")) {
    return state.ledOn ? "LED is ON" : "LED is OFF";
  }

  if (deviceId?.startsWith("door")) {
    if (typeof state.doorState === "string") {
      return `Door is ${state.doorState}`;
    }
    return state.locked ? "Door is LOCKED" : "Door is UNLOCKED";
  }

  if (deviceId?.startsWith("coffee")) {
    return state.isMaking
      ? "Coffee machine is MAKING coffee"
      : "Coffee machine is READY";
  }

  if (deviceId?.startsWith("fan")) {
    return state.fanOn ? "Fan is ON" : "Fan is OFF";
  }

  if (deviceId?.startsWith("servo")) {
    if (state.position === 90) return "Window is OPEN";
    if (state.position === 0) return "Window is CLOSED";
    return `Window position: ${state.position}`;
  }

  return JSON.stringify(state);
}

function getDeviceTitle(deviceId) {
  if (deviceId?.startsWith("light")) return "Light";
  if (deviceId?.startsWith("led")) return "LED Light";
  if (deviceId?.startsWith("door")) return "Door";
  if (deviceId?.startsWith("coffee")) return "Coffee Machine";
  if (deviceId?.startsWith("fan")) return "Fan";
  if (deviceId?.startsWith("servo")) return "Window";
  return deviceId;
}

export default function DevicePage({
  deviceId,
  uiItems,
  state,
  statusMsg,
  actionPending,
  onBack,
  onAction,
}) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%)",
        padding: "24px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "560px",
          background: "#ffffff",
          borderRadius: "18px",
          padding: "32px",
          boxShadow: "0 12px 30px rgba(24, 58, 110, 0.12)",
          border: "1px solid #e3ebf7",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "20px",
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                fontSize: "28px",
                color: "#163a6b",
              }}
            >
              {getDeviceTitle(deviceId)}
            </h2>
            <p
              style={{
                marginTop: "8px",
                marginBottom: 0,
                color: "#5b6b82",
                lineHeight: 1.5,
              }}
            >
              Device ID: {deviceId}
            </p>
          </div>

          <button
            onClick={onBack}
            style={{
              padding: "12px 16px",
              borderRadius: "12px",
              border: "none",
              background: "#1f5fae",
              color: "#ffffff",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Back
          </button>
        </div>

        <div
          style={{
            marginBottom: "20px",
            padding: "16px 18px",
            borderRadius: "14px",
            background: "#f4f8fd",
            border: "1px solid #e0e8f5",
          }}
        >
          <div
            style={{
              fontSize: "14px",
              color: "#5b6b82",
              marginBottom: "6px",
            }}
          >
            Current state
          </div>
          <div
            style={{
              fontSize: "18px",
              fontWeight: 700,
              color: "#163a6b",
            }}
          >
            {getReadableState(deviceId, state)}
          </div>
        </div>

        <div style={{ marginBottom: "20px" }}>
          <h3
            style={{
              marginTop: 0,
              marginBottom: "12px",
              color: "#1c3557",
            }}
          >
            Controls
          </h3>

          {uiItems && uiItems.length > 0 ? (
            <div style={{ display: "grid", gap: "12px" }}>
              {uiItems.map((item, idx) => {
                if (item.type === "button") {
                  const isEnabled = item.enabled !== false && !actionPending;

                  return (
                    <button
                      key={idx}
                      onClick={() => onAction(item.action)}
                      disabled={!isEnabled}
                      title={!isEnabled ? "Device is busy" : undefined}
                      style={{
                        width: "100%",
                        padding: "14px 16px",
                        borderRadius: "12px",
                        border: "none",
                        background: isEnabled ? "#1f5fae" : "#b8c7dc",
                        color: "#ffffff",
                        fontSize: "16px",
                        fontWeight: 600,
                        cursor: isEnabled ? "pointer" : "not-allowed",
                      }}
                    >
                      {actionPending ? "Please wait..." : item.label}
                    </button>
                  );
                }

                return null;
              })}
            </div>
          ) : (
            <div
              style={{
                padding: "16px",
                borderRadius: "12px",
                background: "#f8fbff",
                border: "1px solid #dbe5f2",
                color: "#5b6b82",
              }}
            >
              No UI items available.
            </div>
          )}
        </div>

        <div style={{ marginBottom: "20px" }}>
          <h3
            style={{
              marginTop: 0,
              marginBottom: "12px",
              color: "#1c3557",
            }}
          >
            Raw state
          </h3>

          <pre
            style={{
              background: "#f4f4f4",
              padding: "14px 16px",
              color: "black",
              borderRadius: "12px",
              border: "1px solid #ddd",
              overflowX: "auto",
              margin: 0,
            }}
          >
            {JSON.stringify(state, null, 2)}
          </pre>
        </div>

        <div
          style={{
            padding: "14px 16px",
            borderRadius: "12px",
            background: "#f4f8fd",
            border: "1px solid #e0e8f5",
          }}
        >
          <div
            style={{
              color: "#163a6b",
              fontWeight: 600,
              marginBottom: "6px",
            }}
          >
            Status
          </div>

          <div
            style={{
              color: "#5b6b82",
              fontSize: "14px",
              lineHeight: 1.5,
            }}
          >
            {statusMsg || "Device actions and updates will appear here."}
          </div>
        </div>
      </div>
    </div>
  );
}