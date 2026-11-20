# Reactor Server (`reactor_server`) — Build Checklist

## Phase 1: Docs & Raw Socket Warmup
- [x] Read Python `socket` docs (`bind`, `listen`, `accept`, `recv`, `sendall`) & Socket HOWTO
- [x] Read MDN HTTP/1.1 Message anatomy (Start-line, Headers, `\r\n\r\n`, Body)
- [x] Write a 15-line blocking TCP server (`127.0.0.1:8080`)
- [x] Open `http://127.0.0.1:8080` in browser and print the raw HTTP request bytes
- [x] Send back a hardcoded `HTTP/1.1 200 OK` response and close the socket

## Phase 2: The Reactor Loop (Non-Blocking I/O)
- [x] Set `server_sock.setblocking(False)` and `client_sock.setblocking(False)`
- [x] Create `selectors.DefaultSelector()` and register `server_sock` for `EVENT_READ`
- [x] Write the `while True:` event loop calling `selector.select()`
- [x] Accept new clients in a loop until `BlockingIOError`
- [x] Create a `Connection` class holding `sock`, `readbuffer` (`bytearray`), `writebuffer` (`bytearray`), and `state`
- [x] Dynamically toggle `EVENT_WRITE` only when `write_buffer` is not empty
- [x] Test multiple concurrent `curl` / browser tabs without blocking

## Phase 3: HTTP/1.1 Parser & State Machine
- [x] Buffer incoming bytes until `\r\n\r\n` arrives (handles split TCP packets)
- [x] Parse request line (`method`, `path`, `version`) and headers into a lowercase dictionary
- [x] Handle `Content-Length` bodies by waiting until `len(read_buffer) >= content_length`
- [x] Implement `Transfer-Encoding: chunked` parser (read hex size line -> read data -> stop at `0\r\n\r\n`)
- [x] Support `Connection: keep-alive` (reset request state without closing socket) vs `Connection: close`

## Phase 4: WebSocket Protocol (RFC 6455)
- [ ] Detect `Upgrade: websocket` and `Sec-WebSocket-Key` headers
- [ ] Append magic GUID `258EAFA5-E914-47DA-95CA-C5AB0DC85B11`, hash with `SHA-1`, `base64` encode
- [ ] Send `HTTP/1.1 101 Switching Protocols` and switch connection state to `WEBSOCKET`
- [ ] Decode WebSocket frame header (FIN bit, opcode, mask bit, 7-bit / 16-bit / 64-bit payload length)
- [ ] Unmask client payload bytes using 4-byte XOR key (`payload[i] ^ mask[i % 4]`)
- [ ] Handle control frames (`Ping` -> `Pong`, `Close`) and encode unmasked server replies
- [ ] Test live WebSocket echo from browser DevTools console

## Phase 5: Polish & Stress Test
- [ ] Add build timestamps in code comments
- [ ] Deploy `reactor_server.py` to Oracle Cloud Ubuntu VPS (open port `8080` in firewall/VCN)
- [ ] Run concurrency load test (`wrk` or Python client script with 2,000+ connections) from local PC
- [ ] Push clean code + `README.md` to GitHub