import { useState } from "react";
import smartHomeIcon from "../assets/smart_home.png";

export default function LoginPage({ connected, statusMsg, onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const canSubmit = connected && email.trim() && password.trim();

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f8f7ff",
        fontFamily: "Arial, sans-serif",
      }}
    >
      {/* Top gradient section */}
      <div
        style={{
          height: "320px",
          background: "linear-gradient(180deg, #6f86b6 0%, #0d1333 100%)",
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-start",
          textAlign: "center",
          color: "#ffffff",
          paddingTop: "50px",
          boxSizing: "border-box",
        }}
      >
        <div>
          <img
            src={smartHomeIcon}
            alt="Smart home icon"
            style={{
              width: "90px",
              height: "90px",
              objectFit: "contain",
              marginBottom: "14px",
            }}
          />

          <h1
            style={{
              margin: 0,
              fontSize: "34px",
              fontWeight: 800,
              letterSpacing: "-0.5px",
            }}
          >
            Interactive House
          </h1>

          <p
            style={{
              marginTop: "24px",
              marginBottom: 0,
              fontSize: "20px",
              fontWeight: 400,
              letterSpacing: "0.2px",
            }}
          >
            Control & Monitor Your Smart Home Devices
          </p>
        </div>
      </div>

      {/* Login card */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          marginTop: "-55px",
          padding: "0 24px 40px",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "480px",
            background: "#e9ebf5",
            borderRadius: "28px",
            padding: "30px 32px",
            boxShadow: "0 18px 35px rgba(0, 0, 0, 0.22)",
            boxSizing: "border-box",
          }}
        >
          <h2
            style={{
              margin: 0,
              marginBottom: "24px",
              textAlign: "center",
              fontSize: "28px",
              fontWeight: 800,
              color: "#536899",
            }}
          >
            Welcome
          </h2>

          <div style={{ marginBottom: "18px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "6px",
                marginLeft: "14px",
                fontSize: "16px",
                color: "#536899",
                fontWeight: 500,
              }}
            >
              Email
            </label>

            <input
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: "100%",
                boxSizing: "border-box",
                height: "58px",
                padding: "0 20px",
                borderRadius: "16px",
                border: "3px solid #536899",
                background: "transparent",
                fontSize: "18px",
                color: "#111827",
                outline: "none",
              }}
            />
          </div>

          <div style={{ marginBottom: "24px" }}>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%",
                boxSizing: "border-box",
                height: "58px",
                padding: "0 20px",
                borderRadius: "16px",
                border: "2px solid #8b8f9c",
                background: "transparent",
                fontSize: "18px",
                color: "#111827",
                outline: "none",
              }}
            />
          </div>

          <button
            onClick={() => onLogin(email.trim(), password)}
            disabled={!canSubmit}
            style={{
              width: "100%",
              height: "58px",
              border: "none",
              borderRadius: "18px",
              background: canSubmit ? "#536899" : "#c9cbd6",
              color: canSubmit ? "#ffffff" : "#8f929c",
              fontSize: "18px",
              fontWeight: 700,
              cursor: canSubmit ? "pointer" : "not-allowed",
              transition: "0.2s ease",
            }}
          >
            Log In
          </button>

          {/* Web-only status box */}
          <div
            style={{
              marginTop: "22px",
              padding: "14px 16px",
              borderRadius: "16px",
              background: "#f4f6fc",
              border: "1px solid #d8dceb",
            }}
          >
            <div
              style={{
                marginBottom: "6px",
                color: connected ? "#1d7a46" : "#a15c00",
                fontWeight: 700,
              }}
            >
              Status: {connected ? "Connected to server" : "Not connected to server"}
            </div>

            <div
              style={{
                color: "#5b6478",
                fontSize: "14px",
                lineHeight: 1.5,
              }}
            >
              {statusMsg || "Please enter your credentials to continue."}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}