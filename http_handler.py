def parse_request(request):
    lines = request.split("\r\n")
    # Request line format: "METHOD /path HTTP/version"
    method, path, version = lines[0].split(" ")

    # Parse "Key: Value" headers until the empty line seperator
    header = {}
    for line in lines[1:]:
        if not line:
            break
        key, value = line.split(":", 1)
        header[key.strip().lower()] = value.strip()

    return {
        "method": method,
        "path": path,
        "version": version,
        "header": header
    }

def parse_chunked(body_bytes):
    full_body = b""
    pos = 0 # Read cursor tracking our current byte offset in body_bytes

    while True:
        # Locate the end of the hex chunk_size line "{hex}\r\n"
        line_end = body_bytes.find(b"\r\n", pos)
        if line_end == -1: return None # Incomplete size line; wait for more tcp packets

        # Strip optional chunk extensions and convert hex len to int
        hex_str = body_bytes[pos:line_end].decode().split(";")[0].strip()
        chunk_size = int(hex_str, 16)
        data_start = line_end+2 # skip "\r\n" to reach chunk payload

        # "0\r\n\r\n" signal the end of the chunked stream
        if chunk_size == 0:
            if data_start + 2 > len(body_bytes):
                return None
            return full_body, data_start + 2 # Return the raw body + total bytes consumed
        
        # Ensure full chunk payload and its trailing "\r\n" have arrived
        if data_start+chunk_size+2 >len(body_bytes):
            return None
        
        # append the payload and move cursor past "\r\n"
        full_body+= body_bytes[data_start: data_start +chunk_size]
        pos = data_start+chunk_size+2

def build_response(status,content_length,body, keepalive,content_type):
    connection = "keep-alive" if keepalive else "close"
    return (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {content_length}\r\n"
        f"Connection: {connection}\r\n\r\n"
        f"{body}"
    )
