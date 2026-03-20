import { useState } from "react";

export default function LoginPage({ connected, statusMsg, onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const canSubmit = connected && email.trim() && password.trim();

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%)",
        padding: "24px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          background: "#ffffff",
          borderRadius: "18px",
          padding: "32px",
          boxShadow: "0 12px 30px rgba(24, 58, 110, 0.12)",
          border: "1px solid #e3ebf7",
        }}
      >
        <div style={{ marginBottom: "24px" }}>
          

          <h2
            style={{
              margin: 0,
              fontSize: "28px",
              color: "#163a6b",
            }}
          >
            Interactive House
          </h2>

          <p
            style={{
              marginTop: "8px",
              marginBottom: 0,
              color: "#5b6b82",
              lineHeight: 1.5,
            }}
          >
            Sign in to control and monitor your home devices.
          </p>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label
            style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: 600,
              color: "#24364d",
            }}
          >
            Email
          </label>
          <input
            type="text"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "14px 16px",
              borderRadius: "12px",
              border: "1px solid #cfd9e8",
              fontSize: "16px",
              outline: "none",
            }}
          />
        </div>

        <div style={{ marginBottom: "20px" }}>
          <label
            style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: 600,
              color: "#24364d",
            }}
          >
            Password
          </label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "14px 16px",
              borderRadius: "12px",
              border: "1px solid #cfd9e8",
              fontSize: "16px",
              outline: "none",
            }}
          />
        </div>

        <button
          onClick={() => onLogin(email.trim(), password)}
          disabled={!canSubmit}
          style={{
            width: "100%",
            padding: "14px 16px",
            border: "none",
            borderRadius: "12px",
            background: canSubmit ? "#1f5fae" : "#b8c7dc",
            color: "#ffffff",
            fontSize: "16px",
            fontWeight: 600,
            cursor: canSubmit ? "pointer" : "not-allowed",
            transition: "0.2s ease",
          }}
        >
          Sign in
        </button>

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
              marginBottom: "6px",
              color: connected ? "#1d7a46" : "#a15c00",
              fontWeight: 600,
            }}
          >
            Status: {connected ? "Connected to server" : "Not connected to server"}
          </div>

          <div
            style={{
              color: "#5b6b82",
              fontSize: "14px",
              lineHeight: 1.5,
            }}
          >
            {statusMsg || "Please enter your credentials to continue."}
          </div>
        </div>
      </div>
    </div>
  );
}