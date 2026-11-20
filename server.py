import socket
import selectors

ADDR = '0.0.0.0'
PORT = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((ADDR,PORT))
server.listen(5)
server.setblocking(False)

sel = selectors.DefaultSelector()
sel.register(server, selectors.EVENT_READ,"accept")

def parse_request(request):
    lines = request.split("\r\n")
    head = lines[0].split(" ")
    method, path, version = head[0], head[1], head[2]
    header = dict()
    for line in lines[1:]:
        if not line:
            break
        key, value = line.split(":", 1)
        header[key.strip().lower()] = value.strip()
    print(f"METHOD: {method}\nPATH: {path}\nVERSION: {version}\nHEADER: {header}")
    return {
        "method": method,
        "path": path,
        "version": version,
        "header": header
    }
def route_request(method, path):
    if path == "/":
        status = "200 OK"
        body = "Hello from server"
    elif path == "/about":
        status = "200 OK"
        body = "Server on pure python and socket ig?"
    else:
        status = "404 Not Found"
        body = "Page Not Found"
    content_length = len(body.encode())
    return {
        "status": status,
        "body": body,
        "content_length": content_length
    }

def build_repsonse(status,content_length,body):
    return f"HTTP/1.1 {status}\r\nContent-Length: {content_length}\r\n\r\n{body}"

class Connection:
    def __init__(self,sock):
        self.sock = sock
        self.readbuffer = b""
        self.writebuffer = b""

while True:
    events = sel.select()
    for key, mask in events:
        if key.data == "accept":
            while True:
                try:
                    client, addr = key.fileobj.accept()
                except BlockingIOError:
                    break
                client.setblocking(False)
                conn = Connection(client)
                sel.register(client, selectors.EVENT_READ, conn)
        else:
            conn = key.data
            client = conn.sock
            if mask & selectors.EVENT_READ:
                chunk = client.recv(1024)
                if not chunk:
                    sel.unregister(client)
                    client.close()
                    continue
                conn.readbuffer +=chunk
                if b"\r\n\r\n" not in conn.readbuffer:
                    continue
                request = conn.readbuffer.decode()
                parsed_request = parse_request(request)
                method, path, version, header = parsed_request["method"], parsed_request["path"], parsed_request["version"], parsed_request["header"]
                response_data = route_request(method,path)
                response = build_repsonse(response_data["status"], response_data["content_length"], response_data["body"])
                conn.writebuffer = response.encode()
                sel.modify(client, selectors.EVENT_READ | selectors.EVENT_WRITE, conn)
            if mask & selectors.EVENT_WRITE:
                if conn.writebuffer:
                    send = client.send(conn.writebuffer)
                    conn.writebuffer = conn.writebuffer[send:]
                if not conn.writebuffer:
                    sel.unregister(client)
                    client.close()
