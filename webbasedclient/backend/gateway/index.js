const net = require("net");
const WebSocket = require("ws");
const { WebSocketServer } = WebSocket;

const WS_PORT = Number(process.env.WS_PORT || 3001);
const TCP_HOST = process.env.TCP_HOST || "127.0.0.1";
const TCP_PORT = Number(process.env.TCP_PORT || 5001);

function safeParse(s) {
  try { return [JSON.parse(s), null]; } catch (e) { return [null, e]; }
}

const wss = new WebSocketServer({ port: WS_PORT });
console.log(`[GW] WS listening on ws://localhost:${WS_PORT}`);
console.log(`[GW] TCP target ${TCP_HOST}:${TCP_PORT}`);

wss.on("connection", (ws) => {
  console.log("[GW] WS client connected");

  const sock = net.createConnection({ host: TCP_HOST, port: TCP_PORT });
  let buf = "";

  sock.on("connect", () => console.log("[GW] TCP connected"));

  sock.on("data", (chunk) => {
    buf += chunk.toString("utf8");
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i);
      buf = buf.slice(i + 1);
      if (!line) continue;

      const [msg, err] = safeParse(line);
      if (err) {
        console.warn("[GW] bad JSON from TCP:", err.message);
        continue;
      }

      if (ws.readyState === WebSocket.OPEN) {
        try { ws.send(JSON.stringify(msg)); }
        catch (e) { console.error("[GW] WS send error:", e.message); }
      }
    }
  });

  sock.on("error", (e) => {
    console.error("[GW] TCP error:", e.message);
    try { ws.close(); } catch {}
  });

  sock.on("close", () => {
    console.log("[GW] TCP closed");
    try { ws.close(); } catch {}
  });

  ws.on("message", (data) => {
    const text = data.toString("utf8");
    const [msg, err] = safeParse(text);

    if (err) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: "error",
          sender_id: "gateway",
          payload: { message: "Invalid JSON" }
        }));
      }
      return;
    }

    if (!sock.writable) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: "error",
          sender_id: "gateway",
          payload: { message: "TCP not connected" }
        }));
      }
      return;
    }

    sock.write(JSON.stringify(msg) + "\n");
  });

  ws.on("close", (code, reason) => {
    console.log("[GW] WS closed", code, reason?.toString?.() || "");
    try { sock.end(); } catch {}
  });
});