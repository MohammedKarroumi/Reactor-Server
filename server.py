import socket
import selectors
from http_handler import parse_chunked, parse_request, build_response, process_http
from router import route_request

ADDR = '0.0.0.0'
PORT = 9999

# Create non-blocking TCP listening socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow instant restart 
server.bind((ADDR,PORT))
server.listen(5000)
server.setblocking(False)

# Register listening socket with OS event loop
sel = selectors.DefaultSelector()
sel.register(server, selectors.EVENT_READ,"accept")

class Connection:
    """Per-client state storing incomplete/outgoing byte streams."""
    def __init__(self,sock):
        self.sock = sock
        self.readbuffer = b""
        self.writebuffer = b""
        self.keepalive = False

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
                conn = Connection(client)
                sel.register(client, selectors.EVENT_READ, conn)
        # Existing client socket I/O
        else:
            conn = key.data
            client = conn.sock

            if mask & selectors.EVENT_READ:
                chunk = client.recv(1024)
                if not chunk:
                    # Client closed the TCP connection
                    sel.unregister(client)
                    client.close()
                    continue

                conn.readbuffer +=chunk
                process_http(conn)
                if conn.writebuffer:
                    sel.modify(client, selectors.EVENT_READ | selectors.EVENT_WRITE, conn)

            if mask & selectors.EVENT_WRITE:
                if conn.writebuffer:
                    # Send as many bytes as the OS kernel buffer accepts at the moment
                    send = client.send(conn.writebuffer)
                    conn.writebuffer = conn.writebuffer[send:]
                if not conn.writebuffer:
                    if conn.keepalive:
                        # Stop watching EVENT_WRITE to prevent high cpu usage and wait for next request
                        sel.modify(client, selectors.EVENT_READ, conn)
                    else:
                        sel.unregister(client)
                        client.close()