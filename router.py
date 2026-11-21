import os
import mimetypes

PUBLIC_DIR = os.path.abspath("public")


def route_request(method, path, request_body, content_type="text/plain; charset=utf-8"):
    if method in ("GET", "HEAD"):
        # Strip query parameters (e.g. /style.css?v=1) and map "/" to index.html
        clean_path = path.split("?", 1)[0]
        rel_path = "index.html" if clean_path == "/" else clean_path.lstrip("/")
        full_path = os.path.abspath(os.path.join(PUBLIC_DIR, rel_path))

        # Guard against directory traversal (e.g. /../../server.py)
        if not full_path.startswith(PUBLIC_DIR + os.sep):
            status = "403 Forbidden"
            body = b"403 Forbidden"
            content_type = "text/plain; charset=utf-8"
        elif os.path.isfile(full_path):
            with open(full_path, "rb") as f:
                body = f.read()
            status = "200 OK"
            mime_type, _ = mimetypes.guess_type(full_path)
            content_type = mime_type or "application/octet-stream"
            if content_type.startswith("text/") or content_type == "application/javascript":
                content_type += "; charset=utf-8"
        else:
            status = "404 Not Found"
            body = b"404 Not Found"
            content_type = "text/plain; charset=utf-8"
    elif method == "POST":
        status = "200 OK"
        body = b""
    else:
        status = "405 Method Not Allowed"
        body = b"Method Not Allowed"

    content_length = len(body)
    if method == "HEAD":
        body = b""

    return {
        "status": status,
        "body": body,
        "content_length": content_length,
        "content_type": content_type,
    }