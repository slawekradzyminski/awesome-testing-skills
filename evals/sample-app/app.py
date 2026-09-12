"""Dependency-free localhost sample. Restart to reset its disposable data."""

import argparse
import json
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from domain import ApiError, Store

STATIC = Path(__file__).parent / "static"


def create_server(port=0, audit_path=None):
    store = Store()
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, payload, actor=None, request_body=None, content_type="application/json"):
            data = json.dumps(payload).encode() if content_type == "application/json" else payload
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            if audit_path:
                record = {"time": datetime.now(timezone.utc).isoformat(), "method": self.command,
                          "path": urlsplit(self.path).path, "actor": actor,
                          "request": request_body, "status": status,
                          "response": payload if content_type == "application/json" else None}
                with lock, open(audit_path, "a") as out:
                    out.write(json.dumps(record) + "\n")

        def user(self):
            token = self.headers.get("Authorization", "")
            identities = {"Bearer demo-alice": "alice", "Bearer demo-bob": "bob"}
            if token not in identities:
                raise ApiError(401, "Authentication required")
            return identities[token]

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in ("/", "/cart"):
                return self.respond(200, (STATIC / "index.html").read_bytes(), content_type="text/html")
            if path in ("/app.js", "/style.css"):
                kind = "text/javascript" if path.endswith(".js") else "text/css"
                return self.respond(200, (STATIC / path[1:]).read_bytes(), content_type=kind)
            if path == "/favicon.ico":
                return self.respond(204, b"", content_type="image/x-icon")
            if path == "/health":
                return self.respond(200, {"status": "UP", "version": "sample-1"})
            actor = None
            try:
                actor = self.user()
                if path == "/api/v1/products":
                    return self.respond(200, store.catalog(), actor)
                if path == "/api/v1/cart":
                    return self.respond(200, store.cart(actor), actor)
                raise ApiError(404, "Not found")
            except ApiError as error:
                self.respond(error.status, {"error": error.message}, actor)

        def do_PUT(self):
            actor, body = None, None
            try:
                actor = self.user()
                path = urlsplit(self.path).path
                if not path.startswith("/api/v1/cart/items/"):
                    raise ApiError(404, "Not found")
                length = int(self.headers.get("Content-Length", 0))
                if length > 4096:
                    raise ApiError(413, "Request too large")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ApiError(400, "Expected a JSON object")
                result = store.update(actor, int(path.rsplit("/", 1)[1]), body.get("quantity"))
                self.respond(200, result, actor, body)
            except (ValueError, TypeError):
                self.respond(400, {"error": "Invalid request"}, actor, body)
            except ApiError as error:
                self.respond(error.status, {"error": error.message}, actor, body)

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
