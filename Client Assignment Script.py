"""Chat client.

Usage: python client.py [host] [port]
"""
import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000


def receive(sock):
    """Print everything the server sends until the connection closes."""
    reader = sock.makefile("r", encoding="utf-8", newline="\n")
    for line in reader:
        print(line.rstrip("\n"))
    print("Disconnected from server.")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except OSError as e:
        print(f"Could not connect to {HOST}:{PORT} - {e}")
        return

    t = threading.Thread(target=receive, args=(sock,), daemon=True)
    t.start()

    try:
        while t.is_alive():
            msg = input()
            sock.sendall((msg + "\n").encode("utf-8"))
            if msg.strip() == "/quit":
                break
    except (EOFError, KeyboardInterrupt, OSError):
        pass
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()


if __name__ == "__main__":
    main()
