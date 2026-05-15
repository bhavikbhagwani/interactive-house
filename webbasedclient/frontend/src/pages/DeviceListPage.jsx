export default function DeviceListPage({
  devices,
  deviceStates,
  statusMsg,
  onRefresh,
  onOpenDevice,
  onTriggerScene,
  scenePending,
  role
}) {

  const canUseScenes = role !== "caregiver";

  const scenes = [
    { id: "good_morning", label: "Good Morning" },
    { id: "good_night", label: "Good Night" },
  ];

  function getDeviceTypeLabel(deviceType, deviceId) {
    const type = deviceType?.toLowerCase() || "";
    const id = deviceId?.toLowerCase() || "";

    if (type.includes("led") || type.includes("light")) {
      const number = id.split("-").pop();
      return number ? `Light ${number}` : "Light";
    }

    if (type.includes("fan")) {
      const number = id.split("-").pop();
      return number ? `Fan ${number}` : "Fan";
    }

    if (type.includes("door")) return "Door Lock";
    if (type.includes("servo") || type.includes("window")) return "Window";
    if (type.includes("motion")) return "Motion Sensor";
    if (type.includes("smoke")) return "Smoke Sensor";
    if (type.includes("temp") || type.includes("temperature"))
      return "Steam Sensor";
    if (type.includes("alarm") || type.includes("buzzer")) return "Alarm";
    if (type.includes("coffee")) return "Coffee Machine";

    return deviceType;
  }

  function getDeviceIcon(deviceType) {
    const type = deviceType?.toLowerCase() || "";

    if (type.includes("door")) return "🚪";
    if (type.includes("fan")) return "🌀";
    if (type.includes("servo") || type.includes("window")) return "🪟";
    if (type.includes("motion")) return "🚶";
    if (type.includes("smoke")) return "💨";
    if (type.includes("temp") || type.includes("temperature")) return "🌡️";
    if (type.includes("alarm") || type.includes("buzzer")) return "🚨";
    if (type.includes("coffee")) return "☕";

    return "💡";
  }

  function getStatusText(deviceType, state) {
    if (!state || Object.keys(state).length === 0) {
      return "Unknown";
    }

    const type = deviceType?.toLowerCase() || "";

    if (type.includes("led") || type.includes("light")) {
      const isOn = state.ledOn ?? state.lightOn;
      if (isOn === true) return "ON";
      if (isOn === false) return "OFF";
      return "Unknown";
    }

    if (type.includes("fan")) {
      if (state.fanOn === true) return "ON";
      if (state.fanOn === false) return "OFF";
      return "Unknown";
    }

    if (type.includes("door")) {
      if (typeof state.doorState === "string") return state.doorState;
      if (state.locked === true) return "LOCKED";
      if (state.locked === false) return "UNLOCKED";
      return "Unknown";
    }

    if (type.includes("servo") || type.includes("window")) {
      if (state.position === 90) return "OPEN";
      if (state.position === 0) return "CLOSED";
      return state.position?.toString() || "Unknown";
    }

    if (type.includes("motion")) {
      return state.motionDetected ? "MOTION" : "NO MOTION";
    }

    if (type.includes("smoke")) {
      return state.smokeDetected ? "SMOKE" : "CLEAR";
    }

    if (type.includes("temp") || type.includes("temperature")) {
      return `Level: ${state.temperature}`;
    }

    if (type.includes("alarm") || type.includes("buzzer")) {
      if (state.alarmOn === true || state.buzzerOn === true) return "ON";
      if (state.alarmOn === false || state.buzzerOn === false) return "OFF";
      return "Unknown";
    }

    return "Unknown";
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f8f7ff",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <div
        style={{
          height: "220px",
          background:
            "linear-gradient(180deg, #6f86b6 0%, #2c3e73 45%, #0d1333 100%)",
          color: "#ffffff",
          padding: "48px 38px 0",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            maxWidth: "760px",
            margin: "0 auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "34px",
                fontWeight: 800,
              }}
            >
              Devices
            </h1>

            <p
              style={{
                marginTop: "12px",
                marginBottom: 0,
                fontSize: "18px",
                color: "rgba(255,255,255,0.9)",
              }}
            >
              What would you like to control today?
            </p>
          </div>

          <button
            onClick={onRefresh}
            style={{
              border: "none",
              background: "transparent",
              color: "#ffffff",
              fontSize: "16px",
              fontWeight: 700,
              cursor: "pointer",
              paddingTop: "10px",
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      <div
        style={{
          marginTop: "-34px",
          minHeight: "calc(100vh - 186px)",
          background: "#f8f7ff",
          borderTopLeftRadius: "34px",
          borderTopRightRadius: "34px",
          padding: "28px 24px 40px",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            maxWidth: "680px",
            margin: "0 auto",
            
          }}
        >
          {canUseScenes && (
              
              <div style={{ marginBottom: "22px"}}>
                <div
                  style={{
                    fontSize: "18px",
                    fontWeight: 800,
                    color: "#1f2a5a",
                    marginBottom: "12px",
                    
                  }}
                >
                  Scenes
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: "12px",
                    flexWrap: "wrap",
                  }}
                >
                  {scenes.map((scene) => (
                    <button
                      key={scene.id}
                      onClick={() => onTriggerScene?.(scene.id)}
                      disabled={scenePending}
                      style={{
                        flex: "1 1 180px",
                        padding: "14px 16px",
                        borderRadius: "18px",
                        border: "none",
                        background: "#dce6ff",
                        color: "#1f2a5a",
                        fontSize: "15px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      {scenePending ? "Please wait..." : scene.label}
                    </button>
                  ))}
                </div>
              </div> 
              

            )}

          {devices && devices.length > 0 ? (
            <div
              style={{
                display: "grid",
                gap: "16px",
              }}
            >
              {devices.map((d) => {
                const state = deviceStates?.[d.deviceId];
                const statusText = getStatusText(d.deviceType, state);

                return (
                  <button
                    key={d.deviceId}
                    onClick={() => onOpenDevice(d.deviceId)}
                    style={{
                      width: "100%",
                      display: "flex",
                      alignItems: "center",
                      gap: "18px",
                      textAlign: "left",
                      padding: "20px 24px",
                      borderRadius: "22px",
                      border: "none",
                      background: "#e5e7f0",
                      boxShadow: "0 8px 18px rgba(0, 0, 0, 0.13)",
                      cursor: "pointer",
                    }}
                  >
                    <div
                      style={{
                        width: "56px",
                        height: "56px",
                        borderRadius: "16px",
                        background: "#dce6ff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "26px",
                        flexShrink: 0,
                      }}
                    >
                      {getDeviceIcon(d.deviceType)}
                    </div>

                    <div>
                      <div
                        style={{
                          fontSize: "22px",
                          fontWeight: 800,
                          color: "#5d6473",
                          marginBottom: "6px",
                        }}
                      >
                        {getDeviceTypeLabel(d.deviceType, d.deviceId)}
                      </div>

                      <div
                        style={{
                          fontSize: "16px",
                          color: "#6d7280",
                          marginBottom: "8px",
                        }}
                      >
                        Tap to view controls
                      </div>

                      <span
                        style={{
                          display: "inline-block",
                          padding: "5px 12px",
                          borderRadius: "999px",
                          background: "#dce6ff",
                          color: "#1f2a5a",
                          fontSize: "14px",
                          fontWeight: 700,
                        }}
                      >
                        {statusText}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div
              style={{
                padding: "24px",
                borderRadius: "20px",
                background: "#e5e7f0",
                color: "#6d7280",
                textAlign: "center",
                fontSize: "18px",
              }}
            >
              No devices available
            </div>
          )}

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
              {statusMsg || "Available devices will appear here."}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}