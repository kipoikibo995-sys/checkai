"""Local web app, built on the Python standard library only."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = (Path(__file__).parent / "web.html").read_bytes()
MAX_BODY = 2_000_000


def serve(detector, host: str = "127.0.0.1", port: int = 8000) -> None:
    lock = threading.Lock()  # the model is not safe to run concurrently

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, PAGE, "text/html; charset=utf-8")
            elif self.path == "/api/info":
                info = {"model": bool(detector.scorer),
                        "observer": getattr(detector.scorer, "observer_name", None),
                        "performer": getattr(detector.scorer, "performer_name", None),
                        "calibrated": detector.calibration is not None}
                self._send(200, json.dumps(info).encode(), "application/json")
            else:
                self._send(404, b"Not found", "text/plain")

        def do_POST(self):
            if self.path != "/api/check":
                return self._send(404, b"Not found", "text/plain")
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return self._send(413, b"Text too long", "text/plain")
            try:
                text = json.loads(self.rfile.read(n) or b"{}").get("text", "")
                with lock:
                    report = detector.check(text).to_dict()
                self._send(200, json.dumps(report, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            except Exception as e:  # report the error to the page instead of crashing
                self._send(500, json.dumps({"error": str(e)}, ensure_ascii=False).encode(), "application/json")

        def log_message(self, fmt, *args):
            pass

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Open http://{host}:{port} in your browser  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
