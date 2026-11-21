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
