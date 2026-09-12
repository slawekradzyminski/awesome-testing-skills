"""Deterministic unavailable gateway; evaluator infrastructure, not app source."""
import argparse
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

parser = argparse.ArgumentParser()
parser.add_argument("--ready", type=Path, required=True)
parser.add_argument("--audit", type=Path, required=True)
args = parser.parse_args()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        payload = {"error": "Application temporarily unavailable"}
        data = json.dumps(payload).encode()
        self.send_response(503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Retry-After", "60")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        with args.audit.open("a") as out:
            out.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "method": self.command,
                "path": urlsplit(self.path).path, "status": 503, "actor": None,
                "request": None, "response": payload}) + "\n")
    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET

server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
args.ready.write_text(json.dumps({"pid": os.getpid(), "base_url": f"http://127.0.0.1:{server.server_port}"}))
server.serve_forever()
