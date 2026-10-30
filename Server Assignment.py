"""Multi-client TCP chat server.

Usage: python server.py [host] [port]
"""
import socket
import sys
import threading
from datetime import datetime

HOST = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

clients = {}                 # username -> socket
clients_lock = threading.Lock()


def timestamp():
    return datetime.now().strftime("%H:%M")


def send(sock, text):
    """Send one newline-terminated message; ignore broken sockets."""
    try:
        sock.sendall((text + "\n").encode("utf-8"))
    except OSError:
        pass


def broadcast(text, exclude=None):
    with clients_lock:
        targets = [s for name, s in clients.items() if name != exclude]
    for s in targets:
        send(s, text)


def remove_client(username):
    with clients_lock:
        sock = clients.pop(username, None)
    if sock:
        try:
            sock.close()
        except OSError:
            pass
        broadcast(f"[{timestamp()}] *** {username} left the chat ***")
        print(f"[-] {username} disconnected")


def handle_client(conn, addr):
    reader = conn.makefile("r", encoding="utf-8", newline="\n")
    username = None
    try:
        # --- Registration: ask for a unique username ---
        while True:
            send(conn, "Enter your username:")
            name = reader.readline()
            if not name:
                return
            name = name.strip()
            with clients_lock:
                if not name or " " in name:
                    err = "Username cannot be empty or contain spaces."
                elif name in clients:
                    err = "That username is taken."
                else:
                    clients[name] = conn
                    username = name
                    break
            send(conn, err)

        print(f"[+] {username} connected from {addr[0]}:{addr[1]}")
        send(conn, "Welcome! Commands: /list, /msg <user> <text>, /quit")
        broadcast(f"[{timestamp()}] *** {username} joined the chat ***", exclude=username)

        # --- Main loop ---
        for line in reader:
            line = line.strip()
            if not line:
                continue
            if line == "/quit":
                break
            elif line == "/list":
                with clients_lock:
                    names = ", ".join(sorted(clients))
                send(conn, f"Online: {names}")
            elif line.startswith("/msg "):
                parts = line.split(" ", 2)
                if len(parts) < 3:
                    send(conn, "Usage: /msg <user> <text>")
                    continue
                _, target, text = parts
                with clients_lock:
                    t_sock = clients.get(target)
                if t_sock:
                    send(t_sock, f"[{timestamp()}] (private) {username}: {text}")
                    send(conn, f"[{timestamp()}] (private to {target}): {text}")
                else:
                    send(conn, f"No such user: {target}")
            elif line.startswith("/"):
                send(conn, "Unknown command.")
            else:
                broadcast(f"[{timestamp()}] {username}: {line}")
    except (ConnectionError, OSError):
        pass
    finally:
        if username:
            remove_client(username)
        else:
            conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Chat server listening on {HOST}:{PORT} (Ctrl+C to stop)")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
