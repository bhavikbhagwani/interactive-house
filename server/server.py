"""This module provides the socket functionality for the server."""
import socket
import threading
from serverService import handle_client

PORT = 5001
def main():
    """Start the server and listen for incoming client connections."""
    server_sock = socket.socket()
    server_sock.bind(("localhost", PORT))
    server_sock.listen()

    print(f"Server running on localhost:{PORT}")

    while True:
        client_sock, addr = server_sock.accept()
        thread = threading.Thread(
            target=handle_client,
            args=(client_sock, addr),
            daemon=True
        )
        thread.start()

if __name__ == "__main__":
    main()