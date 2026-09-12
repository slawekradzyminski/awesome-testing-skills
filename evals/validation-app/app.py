"""Disposable orders/profile fixture. Standard library only; loopback only."""

import argparse
import json
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

STATIC = Path(__file__).parent / "static"


def create_server(port=0, audit_path=None):
    state = {"displayName": "Original", "saveCount": 0}
    orders = {"1": {"id": "1", "owner": "alice", "item": "Book"},
              "2": {"id": "2", "owner": "bob", "item": "Pen"}}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, payload, actor=None, request=None, content_type="application/json"):
            data = json.dumps(payload).encode() if content_type == "application/json" else payload
            if audit_path:
                with open(audit_path, "a") as out:
                    out.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                        "method": self.command, "path": urlsplit(self.path).path,
                        "actor": actor, "request": request, "status": status,
                        "response": payload if content_type == "application/json" else None}) + "\n")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlsplit(self.path).path
            with lock:
                if path == "/":
                    return self.respond(200, (STATIC / "index.html").read_bytes(), content_type="text/html")
                if path == "/app.js":
                    return self.respond(200, (STATIC / "app.js").read_bytes(), content_type="text/javascript")
                if path == "/favicon.ico":
                    return self.respond(204, b"", content_type="image/x-icon")
                if path == "/health":
                    return self.respond(200, {"status": "UP", "version": "orders-profile-1"})
                if path == "/api/profile":
                    return self.respond(200, state)
                if path.startswith("/api/orders/"):
                    actor = self.headers.get("X-Test-User")
                    if actor not in ("alice", "bob"):
                        return self.respond(401, {"error": "Authentication required"})
                    order = orders.get(path.removeprefix("/api/orders/"))
                    if not order:
                        return self.respond(404, {"error": "Not found"}, actor)
                    if order["owner"] != actor:
                        return self.respond(403, {"error": "Access denied"}, actor)
                    return self.respond(200, order, actor)
                self.respond(404, {"error": "Not found"})

        def do_POST(self):
            body = None
            with lock:
                if urlsplit(self.path).path != "/api/profile":
                    return self.respond(404, {"error": "Not found"})
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    if not 0 < length <= 4096:
                        return self.respond(400, {"error": "Expected a bounded JSON body"})
                    body = json.loads(self.rfile.read(length))
                    name = body.get("displayName") if isinstance(body, dict) else None
                    if not isinstance(name, str) or not 1 <= len(name) <= 80:
                        return self.respond(400, {"error": "Display name must contain 1 to 80 characters"}, request=body)
                    state["displayName"] = name
                    state["saveCount"] += 1
                    self.respond(200, state, request=body)
                except (ValueError, TypeError):
                    self.respond(400, {"error": "Invalid JSON request"}, request=body)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--ready", type=Path)
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    server = create_server(args.port, args.audit)
    ready = {"pid": os.getpid(), "base_url": f"http://127.0.0.1:{server.server_port}"}
    if args.ready:
        args.ready.write_text(json.dumps(ready))
    print(json.dumps(ready), flush=True)
    server.serve_forever()
