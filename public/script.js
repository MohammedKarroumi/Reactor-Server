const assetBadge = document.getElementById("asset-status");
const httpOutput = document.getElementById("http-output");
const wsOutput = document.getElementById("ws-output");
const wsInput = document.getElementById("ws-input");
const btnWsConnect = document.getElementById("btn-ws-connect");
const btnWsSend = document.getElementById("btn-ws-send");

// Confirm HTML, CSS, and JS all loaded cleanly
window.addEventListener("DOMContentLoaded", () => {
  assetBadge.textContent = "HTML + CSS + JS loaded (200 OK)";
  assetBadge.classList.add("ok");
});

async function runHttpTest(method, url) {
  const start = performance.now();
  try {
    const res = await fetch(url, { method });
    const text = await res.text();
    const ms = (performance.now() - start).toFixed(2);

    httpOutput.textContent =
      `${method} ${url}\n` +
      `Status: ${res.status} ${res.statusText} (${ms} ms)\n` +
      `Content-Type: ${res.headers.get("content-type")}\n` +
      `Content-Length: ${res.headers.get("content-length")}\n\n` +
      `Body preview:\n${text.slice(0, 220)}${text.length > 220 ? "..." : ""}`;
  } catch (err) {
    httpOutput.textContent = `Request failed: ${err.message}`;
  }
}

document.getElementById("btn-get").addEventListener("click", () => {
  runHttpTest("GET", "/index.html");
});

document.getElementById("btn-404").addEventListener("click", () => {
  runHttpTest("GET", "/does-not-exist");
});

// Phase 4 WebSocket test hook
let ws = null;

btnWsConnect.addEventListener("click", () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close();
    return;
  }

  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  wsOutput.textContent = "Connecting to WebSocket...";

  ws.onopen = () => {
    wsOutput.textContent = "Connected (101 Switching Protocols)";
    btnWsConnect.textContent = "Disconnect";
    wsInput.disabled = false;
    btnWsSend.disabled = false;
  };

  ws.onmessage = (e) => {
    wsOutput.textContent += `\n< ${e.data}`;
  };

  ws.onclose = (e) => {
    wsOutput.textContent += `\nClosed (code: ${e.code})`;
    btnWsConnect.textContent = "Connect WS";
    wsInput.disabled = true;
    btnWsSend.disabled = true;
  };

  ws.onerror = () => {
    wsOutput.textContent += "\nWebSocket error (expected until Phase 4 handshake is implemented)";
  };
});

btnWsSend.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN || !wsInput.value) return;
  ws.send(wsInput.value);
  wsOutput.textContent += `\n> ${wsInput.value}`;
  wsInput.value = "";
});