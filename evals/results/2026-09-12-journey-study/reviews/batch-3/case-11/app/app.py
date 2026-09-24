"""Loopback-only disposable Dispatch Desk server; no external services."""
import argparse
import json
import threading
import time
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from domain import Desk

STATIC = Path(__file__).parent / "static"


def create_server(port=0, audit=None):
    desk, lock = Desk(), threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, value, actor=None, body=None, kind="application/json"):
            data = json.dumps(value).encode() if kind == "application/json" else value
            if audit:
                with lock, open(audit, "a") as file:
                    file.write(json.dumps({"at": time.time(), "method": self.command, "path": self.path,
                        "actor": actor, "request": body, "status": status,
                        "response": value if kind == "application/json" else None}) + "\n")
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(data)
            except BrokenPipeError:
                pass

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in ("/", "/app.js", "/style.css"):
                file, kind = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                              "/style.css": ("style.css", "text/css")}[path]
                return self.reply(200, (STATIC / file).read_bytes(), kind=kind)
            if path == "/favicon.ico":
                return self.reply(204, b"", kind="image/x-icon")
            actor = self.headers.get("X-Test-User")
            if actor not in ("alice", "bob"):
                return self.reply(401, {"error": "Choose a fixture user"})
            with lock:
                if path == "/api/orders":
                    status, value = 200, {"orders": desk.visible(actor)}
                elif path.startswith("/api/orders/"):
                    status, value = desk.order(actor, path.split("/")[-1])
                    value = deepcopy(value)
                else:
                    status, value = 404, {"error": "Not found"}
            # Simulates independent fulfillment lookups; requests may complete out of order.
            if path == "/api/orders/A100":
                time.sleep(0.7)
            self.reply(status, value, actor)

        def do_POST(self):
            actor = self.headers.get("X-Test-User")
            if actor not in ("alice", "bob"):
                return self.reply(401, {"error": "Choose a fixture user"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                if not 0 < length <= 8192:
                    raise ValueError()
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError()
            except (ValueError, TypeError):
                return self.reply(400, {"error": "Expected a bounded JSON object"}, actor)
            path = urlsplit(self.path).path
            with lock:
                parts = path.strip("/").split("/")
                if path == "/api/services":
                    status, value = desk.services(actor, body)
                elif len(parts) == 4 and parts[:2] == ["api", "orders"] and parts[3] in ("refund", "address", "note"):
                    status, value = getattr(desk, parts[3])(actor, parts[2], body)
                else:
                    status, value = 404, {"error": "Not found"}
                value = deepcopy(value)
            self.reply(status, value, actor, body)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    server = create_server(audit=args.audit)
    args.ready.write_text(json.dumps({"url": f"http://127.0.0.1:{server.server_port}"}))
    server.serve_forever()
