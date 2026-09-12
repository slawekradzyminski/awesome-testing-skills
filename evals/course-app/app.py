"""Loopback validation fixture. Restart to reset synthetic registrations."""

import argparse
import json
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
from pathlib import Path
from domain import signin, registration_errors


def create_server(port=0, audit_path=None):
    users = {}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, payload, request=None):
            data = json.dumps(payload).encode() if payload is not None else b""
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            if audit_path:
                with open(audit_path, "a") as out:
                    out.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                        "method": self.command, "path": urlsplit(self.path).path,
                        "status": status, "actor": None, "request": request, "response": payload}) + "\n")

        def do_GET(self):
            path = unquote(urlsplit(self.path).path)
            with lock:
                if path == "/health":
                    return self.respond(200, {"status": "UP", "version": "validation-fixture-1"})
                if path.startswith("/api/v1/users/"):
                    user = users.get(path.removeprefix("/api/v1/users/"))
                    return self.respond(200, user) if user else self.respond(404, {"message": "User not found"})
                self.respond(404, {"message": "Not found"})

        def do_POST(self):
            body = None
            with lock:
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    if length > 8192:
                        return self.respond(413, {"message": "Request too large"})
                    body = json.loads(self.rfile.read(length))
                    if not isinstance(body, dict):
                        return self.respond(400, {"message": "Expected a JSON object"}, body)
                    path = urlsplit(self.path).path
                    if path == "/api/v1/users/signin":
                        status, result = signin(body)
                        return self.respond(status, result, body)
                    if path == "/api/v1/users/signup":
                        errors = registration_errors(body)
                        if errors:
                            return self.respond(400, errors, body)
                        name = body["username"]
                        if name in users or any(u["email"] == body["email"] for u in users.values()):
                            return self.respond(409, {"message": "Username or email already exists"}, body)
                        users[name] = {"username": name, "email": body["email"]}
                        return self.respond(201, users[name], body)
                    self.respond(404, {"message": "Not found"}, body)
                except (ValueError, TypeError):
                    self.respond(400, {"message": "Invalid JSON request"}, body)

        def do_DELETE(self):
            path = unquote(urlsplit(self.path).path)
            with lock:
                name = path.removeprefix("/api/v1/users/") if path.startswith("/api/v1/users/") else None
                if name in users:
                    del users[name]
                    return self.respond(204, None)
                self.respond(404, {"message": "User not found"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    server = create_server(audit_path=args.audit)
    args.ready.write_text(json.dumps({"pid": os.getpid(), "base_url": f"http://127.0.0.1:{server.server_port}"}))
    server.serve_forever()
