import { useState } from "react";

export default function LoginPage({ connected, statusMsg, onLogin }) {
const [username, setUsername] = useState("");
const [password, setPassword] = useState("");

return (

 <div className="center">
      <div className="box">        
        <h2>Login</h2>

    <div>
        <input type="text" 
        placeholder="Username" 
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        />
    </div> 

    <div style={{ marginTop: 8 }}>
        <input type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)} />
    </div>

    <div style={{ marginTop: 12 }}>
        <button onClick={() => onLogin(username, password)}
        disabled={!connected}
        >

            Sign in
        </button>
    </div>

    <div style={{ marginTop: 12, color: "gray" }}>
        <div>Connected: {connected ? "Yes" : "No"}</div>
        <div>Status: {statusMsg}</div>

    </div>

    </div>
    </div>
);

}