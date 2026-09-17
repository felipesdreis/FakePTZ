import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import qrcode

from fakeptz.config import CropMode, MACRO_SLOTS, REMOTE_HTTP_PORT


def get_local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())
    finally:
        sock.close()


def build_qr_ascii(url: str) -> str:
    qr = qrcode.QRCode(border=1, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    lines = []
    for y in range(0, len(matrix), 2):
        top = matrix[y]
        bottom = matrix[y + 1] if y + 1 < len(matrix) else [False] * len(top)
        line = "".join(
            "█" if top[x] and bottom[x] else
            "▀" if top[x] else
            "▄" if bottom[x] else
            " "
            for x in range(len(top))
        )
        lines.append(line)
    return "\n".join(lines)


INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FakePTZ Remoto</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f2f0eb; color: #1E3932; }
  h1 { font-size: 1.1rem; text-align: center; color: #006241; }
  .status { background: #fff; border: 2px solid #006241; border-radius: 8px; padding: 10px; margin-bottom: 12px; font-size: 0.9rem; }
  .row { display: flex; gap: 8px; margin-bottom: 8px; }
  button { flex: 1; min-height: 64px; font-size: 1rem; font-weight: bold; border-radius: 8px; border: 2px solid #1E3932; background: #fff; color: #1E3932; }
  button:active { background: #d4e9e2; }
  button.mode.active { background: #00754A; color: #fff; }
  #save.armed { background: #c82014; color: #fff; border-color: #c82014; }
  .dpad { display: grid; grid-template-columns: repeat(3, 64px); grid-template-rows: repeat(3, 64px); gap: 0; width: fit-content; margin: 0 auto 16px; }
  .dpad .corner { background: transparent; }
  .dpad button { background: #1E3932; color: #fff; border: none; font-size: 1.6rem; padding: 0; display: flex; align-items: center; justify-content: center; }
  .dpad button:active { background: #006241; }
  .dpad-up { border-radius: 16px 16px 0 0; }
  .dpad-down { border-radius: 0 0 16px 16px; }
  .dpad-left { border-radius: 16px 0 0 16px; }
  .dpad-right { border-radius: 0 16px 16px 0; }
  .dpad-center { background: #1E3932; display: flex; align-items: center; justify-content: center; }
  .dpad-center span { width: 28px; height: 28px; border-radius: 50%; background: #f2f0eb; }
</style>
</head>
<body>
<h1>FakePTZ — Controle Remoto</h1>
<div class="status" id="status">conectando...</div>

<div class="row">
  <button class="mode" data-mode="ESQUERDA">ESQUERDA</button>
  <button class="mode" data-mode="CENTRO">CENTRO</button>
  <button class="mode" data-mode="DIREITA">DIREITA</button>
</div>

<div class="dpad">
  <div class="corner"></div>
  <button class="dpad-up" data-axis="tilt" data-direction="-1">&#9650;</button>
  <div class="corner"></div>
  <button class="dpad-left" data-axis="pan" data-direction="-1">&#9664;</button>
  <div class="dpad-center"><span></span></div>
  <button class="dpad-right" data-axis="pan" data-direction="1">&#9654;</button>
  <div class="corner"></div>
  <button class="dpad-down" data-axis="tilt" data-direction="1">&#9660;</button>
  <div class="corner"></div>
</div>
<div class="row">
  <button data-axis="zoom" data-direction="-1">Zoom &minus;</button>
  <button data-axis="zoom" data-direction="1">Zoom +</button>
</div>

<div class="row">
  <button data-macro="M1">M1</button>
  <button data-macro="M2">M2</button>
  <button data-macro="M3">M3</button>
  <button id="save">Salvar</button>
</div>

<script>
async function post(path, body) {
  await fetch(path, {
    method: "POST",
    headers: body ? {"Content-Type": "application/json"} : {},
    body: body ? JSON.stringify(body) : undefined,
  });
}

document.querySelectorAll("[data-axis]").forEach(btn => {
  btn.addEventListener("click", () => post("/api/nudge", {
    axis: btn.dataset.axis,
    direction: Number(btn.dataset.direction),
  }));
});

document.querySelectorAll(".mode").forEach(btn => {
  btn.addEventListener("click", () => post("/api/mode", { mode: btn.dataset.mode }));
});

document.querySelectorAll("[data-macro]").forEach(btn => {
  btn.addEventListener("click", () => post("/api/macro", { slot: btn.dataset.macro }));
});

document.getElementById("save").addEventListener("click", () => post("/api/save-armed"));

async function refreshStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    document.getElementById("status").textContent =
      `${data.status} (${data.current_fps.toFixed(0)} FPS) | Z:${data.zoom.toFixed(1)}x P:${(data.pan * 100).toFixed(0)}% T:${(data.tilt * 100).toFixed(0)}% | MODO: ${data.active_mode ?? "LIVRE"}`;
    document.querySelectorAll(".mode").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.mode === data.active_mode);
    });
    document.getElementById("save").classList.toggle("armed", data.save_armed);
  } catch (err) {
    document.getElementById("status").textContent = "desconectado";
  }
}
setInterval(refreshStatus, 500);
refreshStatus();
</script>
</body>
</html>
"""


class _RemoteHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 - assinatura exigida pela stdlib
        pass  # evita corromper a TUI (alt-screen) escrevendo em stderr

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_no_content(self) -> None:
        self.send_response(204)
        self.end_headers()

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        app = self.server.app
        if self.path == "/":
            self._send_html(200, INDEX_HTML)
        elif self.path == "/api/status":
            pipeline = app.pipeline
            self._send_json(
                200,
                {
                    "status": pipeline.status,
                    "current_fps": pipeline.current_fps,
                    "zoom": pipeline.zoom,
                    "pan": pipeline.pan,
                    "tilt": pipeline.tilt,
                    "active_mode": app.active_mode.value if app.active_mode else None,
                    "save_armed": app._save_armed,
                },
            )
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        app = self.server.app
        try:
            body = self._read_json_body()
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "corpo JSON invalido"})
            return

        if self.path == "/api/nudge":
            axis = body.get("axis")
            direction = body.get("direction")
            if axis not in ("pan", "tilt", "zoom") or direction not in (-1, 1):
                self._send_json(400, {"error": "axis/direction invalidos"})
                return
            app.call_from_thread(getattr(app, f"action_nudge_{axis}"), direction)
            self._send_no_content()

        elif self.path == "/api/mode":
            mode = body.get("mode")
            if mode not in CropMode.__members__:
                self._send_json(400, {"error": "mode invalido"})
                return
            app.call_from_thread(app.action_set_mode, mode)
            self._send_no_content()

        elif self.path == "/api/macro":
            slot = body.get("slot")
            if slot not in MACRO_SLOTS:
                self._send_json(400, {"error": "slot invalido"})
                return
            app.call_from_thread(app.action_recall_or_save_macro, slot)
            self._send_no_content()

        elif self.path == "/api/save-armed":
            app.call_from_thread(app.action_toggle_save_armed)
            self._send_json(200, {"save_armed": app._save_armed})

        else:
            self._send_json(404, {"error": "not found"})


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler, app):
        super().__init__(address, handler)
        self.app = app


class RemoteServer:
    def __init__(self, app, port: int = REMOTE_HTTP_PORT):
        self.app = app
        self.port = port
        self.url = None
        self._httpd = None
        self._thread = None

    def start(self) -> str:
        if self._httpd is not None:
            return self.url

        try:
            self._httpd = _Server(("0.0.0.0", self.port), _RemoteHandler, self.app)
        except OSError:
            self._httpd = _Server(("0.0.0.0", 0), _RemoteHandler, self.app)

        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.url = f"http://{get_local_ip()}:{self.port}/"
        return self.url

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
