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
                        return (
                            <button key={idx}
                            style={{ marginRight: 8, marginBottom: 8 }}
                            onClick={() => onAction(item.action)}>
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
          <h3>State</h3>
          <pre style={{ background: "#f4f4f4", padding: 10}}>
            {JSON.stringify(state, null, 2)}
          </pre>

          <div style={{ marginTop: 12, color: "gray" }}>
            Status: {statusMsg}
          </div>
        </div>
    </div>

    );
}