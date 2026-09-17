import http.client
import json
import socket
from types import SimpleNamespace

from fakeptz.config import CropMode, REMOTE_HTTP_PORT
from fakeptz.remote import RemoteServer, build_qr_ascii, get_local_ip


class FakeApp:
    def __init__(self):
        self.pipeline = SimpleNamespace(
            status="ONLINE", current_fps=29.7, zoom=1.4, pan=0.55, tilt=0.5
        )
        self.active_mode = CropMode.CENTRO
        self._save_armed = False
        self.calls = []

    def call_from_thread(self, func, *args):
        func(*args)

    def action_nudge_pan(self, direction):
        self.calls.append(("nudge_pan", direction))

    def action_nudge_tilt(self, direction):
        self.calls.append(("nudge_tilt", direction))

    def action_nudge_zoom(self, direction):
        self.calls.append(("nudge_zoom", direction))

    def action_set_mode(self, mode_value):
        self.calls.append(("set_mode", mode_value))
        self.active_mode = CropMode(mode_value)

    def action_recall_or_save_macro(self, slot):
        self.calls.append(("macro", slot))

    def action_toggle_save_armed(self):
        self._save_armed = not self._save_armed
        self.calls.append(("toggle_save_armed",))


def request(server, method, path, body=None):
    conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=5)
    try:
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if payload else {}
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        data = response.read()
        return response.status, data
    finally:
        conn.close()


def test_get_local_ip_returns_nonempty_string():
    ip = get_local_ip()
    assert isinstance(ip, str)
    assert ip


def test_build_qr_ascii_returns_multiline_ascii_art():
    art = build_qr_ascii("http://192.168.0.10:8642/")
    lines = art.splitlines()
    assert len(lines) > 1
    assert any(ch in art for ch in "█▀▄")


def test_server_serves_index_page():
    server = RemoteServer(FakeApp(), port=0)
    try:
        server.start()
        status, data = request(server, "GET", "/")
        assert status == 200
        assert b"<html" in data.lower()
    finally:
        server.stop()


def test_status_endpoint_reflects_pipeline_state():
    server = RemoteServer(FakeApp(), port=0)
    try:
        server.start()
        status, data = request(server, "GET", "/api/status")
        assert status == 200
        payload = json.loads(data)
        assert payload["status"] == "ONLINE"
        assert payload["zoom"] == 1.4
        assert payload["pan"] == 0.55
        assert payload["tilt"] == 0.5
        assert payload["active_mode"] == "CENTRO"
        assert payload["save_armed"] is False
    finally:
        server.stop()


def test_nudge_endpoint_dispatches_via_call_from_thread():
    app = FakeApp()
    server = RemoteServer(app, port=0)
    try:
        server.start()
        status, _ = request(server, "POST", "/api/nudge", {"axis": "pan", "direction": 1})
        assert status == 204
        assert ("nudge_pan", 1) in app.calls
    finally:
        server.stop()


def test_mode_endpoint_dispatches_via_call_from_thread():
    app = FakeApp()
    server = RemoteServer(app, port=0)
    try:
        server.start()
        status, _ = request(server, "POST", "/api/mode", {"mode": "ESQUERDA"})
        assert status == 204
        assert ("set_mode", "ESQUERDA") in app.calls
    finally:
        server.stop()


def test_macro_endpoint_dispatches_recall_or_save():
    app = FakeApp()
    server = RemoteServer(app, port=0)
    try:
        server.start()
        status, _ = request(server, "POST", "/api/macro", {"slot": "M1"})
        assert status == 204
        assert ("macro", "M1") in app.calls
    finally:
        server.stop()


def test_save_armed_endpoint_toggles_and_returns_state():
    app = FakeApp()
    server = RemoteServer(app, port=0)
    try:
        server.start()
        status, data = request(server, "POST", "/api/save-armed")
        assert status == 200
        assert json.loads(data) == {"save_armed": True}
        assert app._save_armed is True
    finally:
        server.stop()


def test_invalid_nudge_body_returns_400():
    server = RemoteServer(FakeApp(), port=0)
    try:
        server.start()
        status, _ = request(server, "POST", "/api/nudge", {"axis": "sideways", "direction": 1})
        assert status == 400
    finally:
        server.stop()


def test_invalid_mode_returns_400():
    server = RemoteServer(FakeApp(), port=0)
    try:
        server.start()
        status, _ = request(server, "POST", "/api/mode", {"mode": "DIAGONAL"})
        assert status == 400
    finally:
        server.stop()


def test_invalid_macro_slot_returns_400():
    server = RemoteServer(FakeApp(), port=0)
    try:
        server.start()
        status, _ = request(server, "POST", "/api/macro", {"slot": "M9"})
        assert status == 400
    finally:
        server.stop()


def test_unknown_route_returns_404():
    server = RemoteServer(FakeApp(), port=0)
    try:
        server.start()
        status, _ = request(server, "GET", "/nope")
        assert status == 404
    finally:
        server.stop()


def test_start_is_idempotent():
    server = RemoteServer(FakeApp(), port=0)
    try:
        url1 = server.start()
        url2 = server.start()
        assert url1 == url2
    finally:
        server.stop()


def test_start_falls_back_to_ephemeral_port_when_fixed_port_busy():
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("0.0.0.0", REMOTE_HTTP_PORT))
    blocker.listen(1)
    server = RemoteServer(FakeApp())
    try:
        server.start()
        assert server.port != REMOTE_HTTP_PORT
    finally:
        server.stop()
        blocker.close()


def test_stop_releases_the_socket():
    server = RemoteServer(FakeApp(), port=0)
    server.start()
    port = server.port
    server.stop()

    server2 = RemoteServer(FakeApp(), port=port)
    try:
        server2.start()
        assert server2.port == port
    finally:
        server2.stop()
