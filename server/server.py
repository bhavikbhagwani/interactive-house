"""This module provides the socket functionality for the server."""
import socket
import threading
import traceback
from serverService import handle_client
from db_init import initialize_db


PORT = 5001

def main():
    """Start the server and listen for incoming client connections."""
    server_sock = socket.socket()
    server_sock.bind(("0.0.0.0", PORT))
    server_sock.listen()

    print(f"Server running on 0.0.0.0:{PORT}")
    initialize_db()
    print("Demo login: email: user@email.com, password: user123")
    while True:
        client_sock, addr = server_sock.accept()
        threading.Thread(
            target=safe_handle_client,
            args=(client_sock, addr),
            daemon=True
        ).start()

if __name__ == "__main__":
    main()