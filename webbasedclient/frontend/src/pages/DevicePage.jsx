import doorIcon from "../assets/door.png"
import lightIcon from "../assets/lightbulb.png"
import fanIcon from "../assets/fan.png"
import alarmIcon from "../assets/siren.png"
import steamIcon from "../assets/thermometer.png"
import motionIcon from "../assets/motion_sensor.png"
import smokeIcon from "../assets/vape.png"
import windowIcon from "../assets/window.png"


function getDeviceInfo(deviceId) {
  const id = deviceId?.toLowerCase() || "";

  if (id.startsWith("light") || id.startsWith("led")) {
    const number = id.split("-").pop();
    return {
      title: id.startsWith("led") ? `LED Light ${number || ""}` : "Light",
      subtitle: "Control the room lighting",
      icon: lightIcon,
    };
  }

  if (id.startsWith("door")) {
    return {
      title: "Door Lock",
      subtitle: "Manage your home access",
      icon: doorIcon,
    };
  }

  if (id.startsWith("fan")) {
    const number = id.split("-").pop();
    return {
      title: `Fan ${number || ""}`,
      subtitle: "Control the fan",
      icon: fanIcon,
    };
  }

  if (id.startsWith("servo") || id.startsWith("window")) {
    return {
      title: "Window",
      subtitle: "Open or close the window",
      icon: windowIcon,
    };
  }

  if (id.startsWith("motion")) {
    return {
      title: "Motion Sensor",
      subtitle: "Monitor room movement",
      icon: motionIcon,
    };
  }

  if (id.startsWith("smoke")) {
    return {
      title: "Smoke Sensor",
      subtitle: "Monitor smoke detection",
      icon: smokeIcon,
    };
  }

  if (id.startsWith("temp") || id.startsWith("temperature")) {
    return {
      title: "Steam Sensor",
      subtitle: "Monitor humidity",
      icon: steamIcon,
    };
  }

  if (id.startsWith("alarm") || id.startsWith("buzzer")) {
    return {
      title: "Alarm",
      subtitle: "Monitor or control the alarm",
      icon: alarmIcon,
    };
  }

  if (id.startsWith("coffee")) {
    return {
      title: "Coffee Machine",
      subtitle: "Control the coffee machine",
      icon: lightIcon,
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

  if (id.startsWith("light") || id.startsWith("led")) {
    const isOn = state.ledOn ?? state.lightOn;
    if (isOn === true) return "On";
    if (isOn === false) return "Off";
    return "Unknown";
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
    if (state.fanOn === true) return "On";
    if (state.fanOn === false) return "Off";
    return "Unknown";
  }

  if (id.startsWith("servo") || id.startsWith("window")) {
    if (state.position === 90) return "Open";
    if (state.position === 0) return "Closed";
    return state.position !== undefined ? String(state.position) : "Unknown";
  }

  if (id.startsWith("motion")) {
    if (state.motionDetected === true) return "Motion detected";
    if (state.motionDetected === false) return "No motion";
    return "Unknown";
  }

  if (id.startsWith("smoke")) {
    if (state.smokeDetected === true) return "Smoke detected";
    if (state.smokeDetected === false) return "Clear";
    return "Unknown";
  }

  if (id.startsWith("temp") || id.startsWith("temperature")) {
    const level = state.steamLevel ?? state.temperature;
    return level !== undefined ? `Level: ${level}` : "Unknown";
  }

  if (id.startsWith("alarm") || id.startsWith("buzzer")) {
    if (state.alarmOn !== undefined) return state.alarmOn ? "On" : "Off";
    if (state.buzzerOn !== undefined) return state.buzzerOn ? "On" : "Off";
    return "Unknown";
  }

  if (id.startsWith("coffee")) {
    if (state.isMaking === true) return "Making coffee";
    if (state.isMaking === false) return "Ready";
    return "Unknown";
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
  const hasActions = uiItems && uiItems.length > 0;

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
              <img
                  src={deviceInfo.icon}
                  alt="device icon"
                  style={{
                    width: "28px",
                    height: "28px",
                    objectFit: "contain",
                  }}
                />
            </div>

            <h1
              style={{
                margin: 0,
                fontSize: "34px",
                fontWeight: 800,
              }}
            >
              {deviceInfo.title}
            </h1>

            <p
              style={{
                marginTop: "10px",
                marginBottom: 0,
                fontSize: "18px",
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
              fontSize: "16px",
              fontWeight: 700,
              cursor: "pointer",
              paddingTop: "12px",
            }}
          >
            Back
          </button>
        </div>
      </div>

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
          <div
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: "18px",
              padding: "22px 24px",
              borderRadius: "24px",
              background: "#e5e7f0",
              boxShadow: "0 8px 18px rgba(0, 0, 0, 0.13)",
              boxSizing: "border-box",
              marginBottom: "26px",
            }}
          >
            <div
              style={{
                width: "58px",
                height: "58px",
                borderRadius: "18px",
                background: "#dce6ff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "28px",
                flexShrink: 0,
              }}
            >
              <img
                  src={deviceInfo.icon}
                  alt="device icon"
                  style={{
                    width: "28px",
                    height: "28px",
                    objectFit: "contain",
                  }}
                />
            </div>

            <div>
              <div
                style={{
                  fontSize: "18px",
                  fontWeight: 800,
                  color: "#5d6473",
                  marginBottom: "8px",
                }}
              >
                Current Status
              </div>

              <div
                style={{
                  fontSize: "30px",
                  fontWeight: 900,
                  color: "#1f2a5a",
                }}
              >
                {readableState}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: "24px" }}>
            <h2
              style={{
                marginTop: 0,
                marginBottom: "16px",
                fontSize: "22px",
                color: "#363945",
                fontWeight: 800,
              }}
            >
              {hasActions ? "Available Actions" : "Sensor Information"}
            </h2>

            {hasActions ? (
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
                          height: "56px",
                          borderRadius: "20px",
                          border: "none",
                          background: isEnabled ? "#536899" : "#c9cbd6",
                          color: isEnabled ? "#ffffff" : "#8f929c",
                          fontSize: "17px",
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
                  display: "grid",
                  gap: "10px",
                }}
              >
                {state && Object.keys(state).length > 0 ? (
                  Object.entries(state).map(([key, value]) => (
                    <div
                      key={key}
                      style={{
                        padding: "14px 16px",
                        borderRadius: "16px",
                        background: "#e5e7f0",
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "16px",
                        color: "#363945",
                      }}
                    >
                      <strong>{key}</strong>
                      <span>{String(value)}</span>
                    </div>
                  ))
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
                    No state information available.
                  </div>
                )}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}