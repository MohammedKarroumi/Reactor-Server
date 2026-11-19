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
    request = request.split("\r\n")
    head = request[0].split(" ")
    method, path, version = head[0], head[1], head[2]
    print(f"METHOD: {method}\nPATH: {path}\nVERSION: {version}")
    return [method, path, version]

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


while True:
    events = sel.select()
    for key, masl in events:
        if key.data == "accept":
            client, addr = key.fileobj.accept()
            client.setblocking(False)
            sel.register(client,selectors.EVENT_READ, "client")
        elif key.data == "client":
            client = key.fileobj
            request = client.recv(1024).decode()
            if not request.strip():
                client.close()
                sel.unregister(client)
                continue
            method, path, version = parse_request(request)
            response_data = route_request(method,path)
            response = build_repsonse(response_data["status"], response_data["content_length"], response_data["body"])
            response = response.encode()
            sel.unregister(client)
            client.send(response)
            client.close()
