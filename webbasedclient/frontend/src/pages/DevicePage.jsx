function getDeviceInfo(deviceId) {
  const id = deviceId?.toLowerCase() || "";

  if (id.startsWith("light") || id.startsWith("led")) {
    const number = id.split("-").pop();
    return {
      title: id.startsWith("led") ? `LED Light ${number || ""}` : "Light",
      subtitle: "Control the room lighting",
      icon: "💡",
    };
  }

  if (id.startsWith("door")) {
    return {
      title: "Door",
      subtitle: "Control the door",
      icon: "🚪",
    };
  }

  if (id.startsWith("fan")) {
    const number = id.split("-").pop();
    return {
      title: `Fan ${number || ""}`,
      subtitle: "Control the fan",
      icon: "🌀",
    };
  }

  if (id.startsWith("servo") || id.startsWith("window")) {
    return {
      title: "Window",
      subtitle: "Open or close the window",
      icon: "🪟",
    };
  }

  if (id.startsWith("motion")) {
    return {
      title: "Motion Sensor",
      subtitle: "Monitor movement in the house",
      icon: "🚶",
    };
  }

  if (id.startsWith("smoke")) {
    return {
      title: "Smoke Sensor",
      subtitle: "Monitor smoke detection",
      icon: "💨",
    };
  }

  if (id.startsWith("temp") || id.startsWith("temperature")) {
    return {
      title: "Temperature Sensor",
      subtitle: "Monitor room temperature",
      icon: "🌡️",
    };
  }

  if (id.startsWith("alarm") || id.startsWith("buzzer")) {
    return {
      title: "Alarm",
      subtitle: "Monitor or control the alarm",
      icon: "🚨",
    };
  }

  if (id.startsWith("coffee")) {
    return {
      title: "Coffee Machine",
      subtitle: "Control the coffee machine",
      icon: "☕",
    };
  }

  return {
    title: deviceId,
    subtitle: "Control your connected device",
    icon: "💡",
  };
}

function getReadableState(deviceId, state) {
  if (!state || Object.keys(state).length === 0) return "Unknown";

  const id = deviceId?.toLowerCase() || "";

  if (id.startsWith("light")) {
    return state.lightOn ? "On" : "Off";
  }

  if (id.startsWith("led")) {
    return state.ledOn ? "On" : "Off";
  }

  if (id.startsWith("door")) {
    if (typeof state.doorState === "string") {
      return state.doorState.charAt(0).toUpperCase() + state.doorState.slice(1);
    }
    if (state.locked === true) return "Locked";
    if (state.locked === false) return "Unlocked";
    return "Unknown";
  }

  if (id.startsWith("fan")) {
    return state.fanOn ? "On" : "Off";
  }

  if (id.startsWith("servo") || id.startsWith("window")) {
    if (state.position === 90) return "Open";
    if (state.position === 0) return "Closed";
    return state.position !== undefined ? String(state.position) : "Unknown";
  }

  if (id.startsWith("motion")) {
    return state.motionDetected ? "Motion detected" : "No motion";
  }

  if (id.startsWith("smoke")) {
    return state.smokeDetected ? "Smoke detected" : "Clear";
  }

  if (id.startsWith("temp") || id.startsWith("temperature")) {
    return state.temperature !== undefined ? `${state.temperature}°C` : "Unknown";
  }

  if (id.startsWith("alarm") || id.startsWith("buzzer")) {
    if (state.alarmOn !== undefined) return state.alarmOn ? "On" : "Off";
    if (state.buzzerOn !== undefined) return state.buzzerOn ? "On" : "Off";
    return "Unknown";
  }

  if (id.startsWith("coffee")) {
    return state.isMaking ? "Making coffee" : "Ready";
  }

  return "Unknown";
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
  const deviceInfo = getDeviceInfo(deviceId);
  const readableState = getReadableState(deviceId, state);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f8f7ff",
        fontFamily: "Arial, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          height: "240px",
          background:
            "linear-gradient(180deg, #6f86b6 0%, #2c3e73 45%, #0d1333 100%)",
          color: "#ffffff",
          padding: "48px 38px 0",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            maxWidth: "720px",
            margin: "0 auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <div
              style={{
                width: "62px",
                height: "62px",
                borderRadius: "18px",
                background: "rgba(255,255,255,0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "30px",
                marginBottom: "14px",
              }}
            >
              {deviceInfo.icon}
            </div>

            <h1
              style={{
                margin: 0,
                fontSize: "38px",
                fontWeight: 800,
              }}
            >
              {deviceInfo.title}
            </h1>

            <p
              style={{
                marginTop: "10px",
                marginBottom: 0,
                fontSize: "20px",
                color: "rgba(255,255,255,0.92)",
              }}
            >
              {deviceInfo.subtitle}
            </p>
          </div>

          <button
            onClick={onBack}
            style={{
              border: "none",
              background: "transparent",
              color: "#ffffff",
              fontSize: "18px",
              fontWeight: 700,
              cursor: "pointer",
              paddingTop: "12px",
            }}
          >
            Back
          </button>
        </div>
      </div>

      {/* Main rounded content area */}
      <div
        style={{
          marginTop: "-34px",
          minHeight: "calc(100vh - 206px)",
          background: "#f8f7ff",
          borderTopLeftRadius: "34px",
          borderTopRightRadius: "34px",
          padding: "32px 24px 40px",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            maxWidth: "680px",
            margin: "0 auto",
          }}
        >
          {/* Current status card */}
          <div
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: "20px",
              padding: "24px 28px",
              borderRadius: "24px",
              background: "#e5e7f0",
              boxShadow: "0 10px 22px rgba(0, 0, 0, 0.15)",
              boxSizing: "border-box",
              marginBottom: "28px",
            }}
          >
            <div
              style={{
                width: "62px",
                height: "62px",
                borderRadius: "18px",
                background: "#dce6ff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "28px",
                flexShrink: 0,
              }}
            >
              {deviceInfo.icon}
            </div>

            <div>
              <div
                style={{
                  fontSize: "20px",
                  fontWeight: 800,
                  color: "#5d6473",
                  marginBottom: "8px",
                }}
              >
                Current Status
              </div>

              <div
                style={{
                  fontSize: "34px",
                  fontWeight: 900,
                  color: "#1f2a5a",
                }}
              >
                {readableState}
              </div>
            </div>
          </div>

          {/* Available actions */}
          <div style={{ marginBottom: "24px" }}>
            <h2
              style={{
                marginTop: 0,
                marginBottom: "16px",
                fontSize: "24px",
                color: "#363945",
                fontWeight: 800,
              }}
            >
              Available Actions
            </h2>

            {uiItems && uiItems.length > 0 ? (
              <div style={{ display: "grid", gap: "16px" }}>
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
                          height: "58px",
                          borderRadius: "20px",
                          border: "none",
                          background: isEnabled ? "#536899" : "#c9cbd6",
                          color: isEnabled ? "#ffffff" : "#8f929c",
                          fontSize: "18px",
                          fontWeight: 800,
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
                  padding: "18px",
                  borderRadius: "18px",
                  background: "#e5e7f0",
                  color: "#6d7280",
                  fontSize: "16px",
                }}
              >
                No actions available for this device.
              </div>
            )}
          </div>

          {/* Web-only status box */}
          <div
            style={{
              marginTop: "24px",
              padding: "16px 18px",
              borderRadius: "18px",
              background: "#eef1fa",
              border: "1px solid #d9deee",
            }}
          >
            <div
              style={{
                color: "#1f2a5a",
                fontWeight: 800,
                marginBottom: "6px",
              }}
            >
              Status
            </div>

            <div
              style={{
                color: "#5b6478",
                fontSize: "14px",
                lineHeight: 1.5,
              }}
            >
              {statusMsg || "Device actions and updates will appear here."}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}