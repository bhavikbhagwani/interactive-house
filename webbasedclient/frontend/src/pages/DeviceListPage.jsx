function getDeviceTypeLabel(device) {
  const type = device.deviceType || "";
  const id = device.deviceId || "";

  if (type === "light" || id.startsWith("light") || id.startsWith("led")) {
    return "Light";
  }

  if (type === "door" || type === "door_lock" || id.startsWith("door")) {
    return "Door Lock";
  }

  if (type === "coffee_machine" || id.startsWith("coffee")) {
    return "Coffee Machine";
  }

  if (type === "fan" || id.startsWith("fan")) {
    return "Fan";
  }

  if (type === "window" || type === "servo" || id.startsWith("window") || id.startsWith("servo")) {
    return "Window";
  }

  if (type === "motion_sensor" || id.startsWith("motion")) {
    return "Motion Sensor";
  }

  if (type === "smoke_sensor" || id.startsWith("smoke")) {
    return "Smoke Sensor";
  }

  if (type === "temperature_sensor" || id.startsWith("temp")) {
    return "Temperature Sensor";
  }

  if (type === "alarm" || id.startsWith("alarm") || id.startsWith("buzzer")) {
    return "Alarm";
  }

  return type || "Unknown Device";
}

export default function DeviceListPage({
  devices,
  statusMsg,
  onRefresh,
  onOpenDevice,
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
            alignItems: "center",
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
              Devices
            </h2>
            <p
              style={{
                marginTop: "8px",
                marginBottom: 0,
                color: "#5b6b82",
                lineHeight: 1.5,
              }}
            >
              Select a device to view its controls and current information.
            </p>
          </div>

          <button
            onClick={onRefresh}
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
            Refresh
          </button>
        </div>

        <div style={{ marginTop: "20px" }}>
          {devices && devices.length > 0 ? (
            <div style={{ display: "grid", gap: "12px" }}>
              {devices.map((d) => (
                <button
                  key={d.deviceId}
                  onClick={() => onOpenDevice(d.deviceId)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "18px 20px",
                    borderRadius: "14px",
                    border: "1px solid #dbe5f2",
                    background: "#f8fbff",
                    cursor: "pointer",
                  }}
                >
                  <div
                    style={{
                      fontSize: "18px",
                      fontWeight: 600,
                      color: "#1c3557",
                      marginBottom: "6px",
                    }}
                  >
                    {getDeviceTypeLabel(d)}
                  </div>
                  <div
                    style={{
                      fontSize: "14px",
                      color: "#5b6b82",
                    }}
                  >
                    Device ID: {d.deviceId}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div
              style={{
                padding: "20px",
                borderRadius: "14px",
                background: "#f8fbff",
                border: "1px solid #dbe5f2",
                color: "#5b6b82",
              }}
            >
              No devices found.
            </div>
          )}
        </div>

        <div
          style={{
            marginTop: "20px",
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
            {statusMsg || "Available devices will appear here."}
          </div>
        </div>
      </div>
    </div>
  );
}