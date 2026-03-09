
export class WsClient {
  constructor({ onMessage, onStatus }) {
    this.ws = null;
    this.onMessage = onMessage;
    this.onStatus = onStatus;
  }

  connect(url) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.onStatus?.({ connected: true });
    };

    this.ws.onclose = (ev) => {
      this.onStatus?.({ connected: false, reason: `closed (${ev.code})` });
      this.ws = null;
    };

    this.ws.onerror = () => {
      this.onStatus?.({ connected: false, reason: "socket error" });
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.onMessage?.(msg);
      } catch (e) {
        console.error("WS parse error:", e, event.data);
      }
    };
  }

  disconnect() {
    if (this.ws) this.ws.close();
    this.ws = null;
    this.onStatus?.({ connected: false, reason: "manual disconnect" });
  }

  send(msg) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("WS not connected; cannot send:", msg);
      return;
    }
    this.ws.send(JSON.stringify(msg));
  }
}