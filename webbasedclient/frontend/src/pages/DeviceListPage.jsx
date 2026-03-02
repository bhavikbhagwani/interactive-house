export default function DeviceListPage({
    devices, 
    statusMsg, 
    onRefresh, 
    onOpenDevice,
}) {
    return (
 <div className="center">
      <div className="box">           
         <h2>Devices</h2>

            <button onClick={onRefresh}>Refresh</button>

            <ul style={{ marginTop: 12 }}>
                {devices && devices.length > 0 ? (
                    devices.map((d) => (
                        <li key={d.deviceId} style={{ marginBottom: 6 }}>
                            <button onClick={() => onOpenDevice(d.deviceId)}>
                                {d.deviceId} ({d.deviceType})
                            </button>
                        </li>
                    ))
                ) : (

                <li>No devices found</li>
                )}

            </ul>
            <div style={{ marginTop: 12, color: "gray" }}>
                Status: {statusMsg}
            </div>

        </div>
        </div>
    );
} 