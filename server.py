import socket
import selectors
from http_handler import parse_chunked, parse_request, build_response
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

def route_request(method, path, request_body, content_type= "text/plain; charset=utf-8"):
    if method == "GET":
        if path == "/":
            status = "200 OK"
            body = "Hello from server"
        elif path == "/about":
            status = "200 OK"
            body = "Server on pure python and socket ig?"
        else:
            status = "404 Not Found"
            body = "Page Not Found"
    elif method == "POST":
        status = "200 OK"
        body = ""
    else:
        status = "405 Method Not Allowed"
        body = "Method Not Allowed"
    # Measure byte length (not char count)
    content_length = len(body.encode())
    return {
        "status": status,
        "body": body,
        "content_length": content_length,
        "content_type": content_type
    }



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

                # Wait until the full HTTP header block "\r\n\r\n" has arrived
                if b"\r\n\r\n" not in conn.readbuffer:
                    continue

                # Split the request into header and body
                header_bytes, body_bytes = conn.readbuffer.split(b"\r\n\r\n",1)
                parsed_header = parse_request(header_bytes.decode())
                
                # Assign values to method, path, version and header
                method, path, version, header= (
                    parsed_header["method"], 
                    parsed_header["path"], 
                    parsed_header["version"], 
                    parsed_header["header"]
                )

                # HTTP/1.1 defaults to persistent connection unless "Connection: close" is sent
                conn_header = header.get("connection", "").lower()
                if version == "HTTP/1.1":
                    conn.keepalive = (conn_header != "close")
                # HTTP/1.0 default to non-persistent connection unless "Connection: keep-alive" is sent
                else:
                    conn.keepalive = (conn_header == "keep-alive")
                
                # Extract request body (either chunked stream or fixed content-length)
                if header.get("transfer-encoding", "").lower() == "chunked":
                    result = parse_chunked(body_bytes)
                    if result is None:
                        continue # Wait for remaining chunks
                    raw_body, consumed = result
                    request_body = raw_body.decode()
                    conn.readbuffer = body_bytes[consumed:]
                else:
                    content_length = int(header.get("content-length", 0))
                    if len(body_bytes) < content_length:
                        continue # Wait for remaining body bytes
                    request_body = body_bytes[:content_length].decode()
                    conn.readbuffer = body_bytes[content_length:]
                
                # Build HTTP response and watch socket for write readiness
                response_data = route_request(method,path,request_body)
                response = build_response(
                    response_data["status"],
                    response_data["content_length"],
                    response_data["body"],
                    conn.keepalive,
                    response_data["content_type"]
                    )
                conn.writebuffer = response.encode()
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