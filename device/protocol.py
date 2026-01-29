import json
import socket
from typing import Any, Dict, Optional

def send_json(sock: socket.socket, msg: Dict[str, Any]) -> None:
    """
    Send one JSON message over TCP using newline-delimited JSON (NDJSON).
    """
    data = json.dumps(msg, separators=(",", ":")).encode("utf-8") + b"\n"
    sock.sendall(data)

def recv_json_line(buffered) -> Optional[Dict[str, Any]]:
    """
    Read exactly one JSON message (one line) from a buffered socket.
    Returns a dict, or None if the connection is closed.
    """
    line = buffered.readline()
    if not line:
        return None
    return json.loads(line)
