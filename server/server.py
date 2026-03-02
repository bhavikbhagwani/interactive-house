"""This module provides the socket functionality for the server."""
import socket
import threading
import traceback
from serverService import handle_client

PORT = 5001

def safe_handle_client(client_sock, addr):
    try:
        print(f"[+] client connected from {addr}", flush=True)
        handle_client(client_sock, addr)
    except Exception:
        print("[!] handle_client crashed:", flush=True)
        traceback.print_exc()
    finally:
        try:
            client_sock.close()
        except Exception:
            pass
        print(f"[-] client closed {addr}", flush=True)

def main():
    """Start the server and listen for incoming client connections."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # IMPORTANT: accept connections from emulator/other devices
    server_sock.bind(("0.0.0.0", PORT))
    server_sock.listen(50)

    print(f"Server running on 0.0.0.0:{PORT}", flush=True)

    while True:
        client_sock, addr = server_sock.accept()
        threading.Thread(
            target=safe_handle_client,
            args=(client_sock, addr),
            daemon=True
        ).start()

if __name__ == "__main__":
    main()