# Reactor Server

A lightweight, single-threaded **HTTP/1.1** (and upcoming **WebSocket**) server built from scratch in pure Python using only the standard library (`socket`, `selectors`, `os`, `mimetypes`).

Built from first principles with zero external frameworks or dependencies to explore non-blocking I/O, OS-level event multiplexing, and manual TCP byte-stream framing.

---

## Features

- **Single-Threaded Reactor Event Loop:** Uses `selectors.DefaultSelector()` (`epoll` / `kqueue` / `select`) with non-blocking sockets to handle thousands of concurrent connections on a single thread.
- **Manual HTTP/1.1 Framing:** Per-connection `readbuffer` and `writebuffer` state machines to reassemble fragmented TCP packets across `\r\n\r\n` header boundaries.
- **Body Parsing:** Supports fixed `Content-Length` payloads as well as hex-delimited `Transfer-Encoding: chunked` streams (including pipelined request preservation).
- **Persistent Connections:** Full HTTP/1.1 `Connection: keep-alive` and HTTP/1.0 connection lifecycle management.
- **Static File Serving & Security:** Serves `GET` and `HEAD` assets from `public/` (defaulting `/` to `index.html`) with automatic MIME type detection and `os.path.abspath` path-traversal protection (`403 Forbidden`).

---

## Project Structure

```text
Reactor-Server/
├── server.py         # Non-blocking Reactor loop, socket lifecycle, and per-client byte buffers
├── http_handler.py   # HTTP/1.1 request parser, chunked transfer decoder, and response builder
├── router.py         # Static file router, MIME type detection, and directory traversal guard
└── public/           # Browser test bench (index.html, style.css, script.js)
```

---

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MohammedKarroumi/Reactor-Server.git
   cd Reactor-Server
   ```

2. **Run the server:**
   ```bash
   python3 server.py
   ```
   The server binds to `0.0.0.0:9999` by default.

3. **Open in your browser:**
   Visit `http://127.0.0.1:9999` to load the static test bench.

---

## Roadmap

- [x] Non-blocking TCP server with `selectors` Reactor loop
- [x] HTTP/1.1 request line & header parser
- [x] `Content-Length` and `Transfer-Encoding: chunked` body framing
- [x] Persistent `keep-alive` connections (verified at 5,000 concurrent requests)
- [x] Modular architecture (`server.py`, `http_handler.py`, `router.py`)
- [x] Static file server (`public/`) with MIME types & path-traversal protection
- [ ] WebSocket protocol upgrade (`101 Switching Protocols` handshake)
- [ ] Binary WebSocket frame parser, unmasking, and full-duplex echo/broadcast

---

## Notes

- I wrote all core Python files (`server.py`, `http_handler.py`, `router.py`) from scratch, implementing the Reactor loop, HTTP/1.1 parser, and static router by hand.
- The local browser test bench (`public/`) and documentation formatting were AI-assisted.

