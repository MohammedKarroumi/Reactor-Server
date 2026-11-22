import socket
import selectors
from http_handler import parse_chunked, parse_request, build_response, process_http
from router import route_request

ADDR = '0.0.0.0'
PORT = 9999

# Create non-blocking TCP listening socket
print("Starting Reactor server...")
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow instant restart 
server.bind((ADDR,PORT))
server.listen(5000)
server.setblocking(False)

# Register listening socket with OS event loop
print(f"Server running on port:{PORT}")
sel = selectors.DefaultSelector()
sel.register(server, selectors.EVENT_READ,"accept")

class Connection:
    """Per-client state storing incomplete/outgoing byte streams."""
    def __init__(self,sock,addr):
        self.sock = sock
        self.addr = f"{addr[0]}:{addr[1]}"
        self.readbuffer = b""
        self.writebuffer = b""
        self.keepalive = False

def log_http(direction, addr, raw_bytes):
    """Safely prints HTTP headers and first line without dumping raw binary files."""
    if not raw_bytes:
        return
    # Split headers from body so we don't print raw image/zip bytes
    header_part = raw_bytes.split(b"\r\n\r\n", 1)[0]
    text = header_part.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if lines:
        print(f"\n{direction} [{addr}] {lines[0]}")
        for h in lines[1:]:
            print(f"    {h}")

# Mainn Reactor event loop
while True:
    events = sel.select() # Block until at least one socket is ready
    for key, mask in events:
        # New incoming client connection
        if key.data == "accept":
            while True:
                try:
                    client, addr = key.fileobj.accept()
                except BlockingIOError:
                    break # no more pending connection in backlog
                client.setblocking(False)
                conn = Connection(client,addr)
                sel.register(client, selectors.EVENT_READ, conn)
                print(f"[+] Connected: {conn.addr}")
        # Existing client socket I/O
        else:
            conn = key.data
            client = conn.sock

            if mask & selectors.EVENT_READ:
                chunk = client.recv(1024)
                if not chunk:
                    # Client closed the TCP connection
                    print(f"[-] Disconnected: {conn.addr}")
                    sel.unregister(client)
                    client.close()
                    continue
                print(f"[<] {conn.addr} received {len(chunk)} bytes")
                conn.readbuffer +=chunk

                if b"\r\n\r\n" in conn.readbuffer:
                    log_http("[ --> ] REQ", conn.addr, conn.readbuffer)
                
                process_http(conn)
                if conn.writebuffer:
                    log_http("[ <-- ] RES", conn.addr, conn.writebuffer)
                    sel.modify(client, selectors.EVENT_READ | selectors.EVENT_WRITE, conn)

            if mask & selectors.EVENT_WRITE:
                if conn.writebuffer:
                    # Send as many bytes as the OS kernel buffer accepts at the moment
                    send = client.send(conn.writebuffer)
                    conn.writebuffer = conn.writebuffer[send:]
                    print(f"[>] {conn.addr} sent {send} bytes")
                if not conn.writebuffer:
                    if conn.keepalive:
                        # Stop watching EVENT_WRITE to prevent high cpu usage and wait for next request
                        print(f"[*] {conn.addr} keeping connection alive")
                        sel.modify(client, selectors.EVENT_READ, conn)
                    else:
                        print(f"[-] Closed after response: {conn.addr}")
                        sel.unregister(client)
                        client.close()