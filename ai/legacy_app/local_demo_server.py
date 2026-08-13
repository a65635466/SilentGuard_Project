"""Local-only web server for viewing an Agent request and response."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .risk_segments import AgentError
from .silentguard_agent import SilentGuardAgent


APP_DIR = Path(__file__).parent
SAMPLE_INPUT = APP_DIR / "sample_input.json"


def read_mock() -> dict[str, Any]:
    return json.loads(SAMPLE_INPUT.read_text(encoding="utf-8"))


class DemoHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._send(200, (APP_DIR / "demo.html").read_bytes(), "text/html; charset=utf-8")
            return
        if self.path == "/api/mock":
            body = json.dumps(read_mock(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return
        self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/analyze":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = SilentGuardAgent().analyze_incident(payload)
            body = json.dumps({"ok": True, "result": result}, ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
        except (ValueError, OSError, AgentError) as exc:
            body = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self._send(500, body, "application/json; charset=utf-8")

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[local-demo] {format % args}")


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), DemoHandler)
    print(f"SilentGuard local demo: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    finally:
        server.server_close()
