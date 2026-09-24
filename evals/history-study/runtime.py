"""Owned native historical runtimes and an audited loopback gateway. Evaluator only."""
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import socket
import subprocess
import threading
import time
from urllib.parse import urlsplit, unquote

ADMIN = {'username': 'history_admin', 'password': 'HistoryAdminPass123!'}
CUSTOMER = {'username': 'history_customer', 'password': 'HistoryCustomer123!'}


def request(url, method='GET', body=None, token=None):
    parsed = urlsplit(url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=15)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    payload = json.dumps(body).encode() if body is not None else None
    conn.request(method, parsed.path + ('?' + parsed.query if parsed.query else ''), payload, headers)
    response = conn.getresponse()
    raw = response.read()
    result = {'status': response.status, 'body': raw.decode(errors='replace')}
    conn.close()
    try:
        result['json'] = json.loads(result['body'])
    except ValueError:
        pass
    return result


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class Runtime:
    def __init__(self, build, control, backend='runtime-backend', frontend=None, outage=False):
        self.build, self.control = Path(build), Path(control)
        self.backend, self.frontend, self.outage = backend, frontend, outage
        self.proc = self.server = None
        self.legacy = bool(frontend and frontend.startswith('cart-'))
        self.api_server = None
        self.control.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.audit = []

    def start(self):
        try:
            if not self.outage:
                self.start_native()
            runtime = self

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *_):
                    pass

                def handle_request(self):
                    path = urlsplit(self.path).path
                    started = time.time()
                    payload = self.rfile.read(int(self.headers.get('Content-Length', '0')))
                    head_length = None
                    is_api = (not runtime.frontend or (runtime.legacy and self.server.server_port == 4001)
                              or path.startswith(('/api/', '/actuator', '/v3/', '/swagger')))
                    headers = {}
                    if runtime.outage:
                        status, raw = 503, b'{"error":"Service temporarily unavailable"}'
                        headers['Content-Type'] = 'application/json'
                    elif is_api:
                        conn = http.client.HTTPConnection('127.0.0.1', runtime.native_port, timeout=20)
                        forwarded = {k: v for k, v in self.headers.items()
                                     if k.lower() not in ('host', 'connection', 'accept-encoding')}
                        # Preserve the external Host: ordinary same-origin reverse proxy behavior.
                        forwarded['Host'] = self.headers.get('Host', '')
                        try:
                            conn.request(self.command, self.path, payload, forwarded)
                            response = conn.getresponse()
                            status, raw = response.status, response.read()
                            if self.command == 'HEAD':
                                head_length = response.getheader('Content-Length')
                            headers = {k: v for k, v in response.getheaders()
                                       if k.lower() not in ('transfer-encoding', 'connection', 'content-length')}
                        except (OSError, http.client.HTTPException) as exc:
                            status, raw = 502, json.dumps({'gateway_error': type(exc).__name__}).encode()
                        finally:
                            conn.close()
                        if runtime.frontend and self.command == 'GET':
                            # Same controlled delivery latency in every UI arm and fixed contrast.
                            time.sleep(1.8 if re.fullmatch(r'/api/v1/products/\d+', path) else .08)
                    else:
                        root = (runtime.build/runtime.frontend/'dist').resolve()
                        file = (root/unquote(path).lstrip('/')).resolve()
                        if not file.is_relative_to(root):
                            status, raw = 403, b'Forbidden'
                        else:
                            if not file.is_file():
                                file = root/'index.html'
                            status, raw = 200, file.read_bytes()
                            headers['Content-Type'] = mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
                    self.send_response(status)
                    for key, value in headers.items():
                        if key.lower() not in ('content-length', 'connection', 'transfer-encoding'):
                            self.send_header(key, value)
                    self.send_header('Content-Length', head_length if head_length is not None else str(len(raw)))
                    self.send_header('Connection', 'close')
                    if not is_api:
                        self.send_header('Content-Security-Policy', "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'" + (' http://localhost:4001' if runtime.legacy else ''))
                    self.end_headers()
                    try:
                        if self.command != 'HEAD':
                            self.wfile.write(raw)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    with runtime.lock:
                        entry = {'id': len(runtime.audit)+1, 'at': started, 'method': self.command,
                                 'path': self.path, 'status': status, 'api': is_api,
                                 'request_sha256': hashlib.sha256(payload).hexdigest(),
                                 'response_sha256': hashlib.sha256(raw).hexdigest(),
                                 'seconds': round(time.time()-started, 3)}
                        runtime.audit.append(entry)
                        with open(runtime.control/'audit.jsonl', 'a') as log:
                            log.write(json.dumps(entry)+'\n')

                do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = handle_request

            if self.legacy:
                self.api_server = ThreadingHTTPServer(('127.0.0.1',4001),Handler)
                threading.Thread(target=self.api_server.serve_forever,daemon=True).start()
            self.server = ThreadingHTTPServer(('127.0.0.1', 8081 if self.legacy else 0), Handler)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            self.url = 'http://127.0.0.1:' + str(self.server.server_port)
            return self
        except BaseException:
            self.stop()
            raise

    def start_native(self):
        modern = self.backend == 'runtime-backend'
        tools_file=self.build/'runtime-tools.json'
        tools=json.loads(tools_file.read_text()) if tools_file.exists() else {}
        key='java25' if modern else 'java21'
        java=(Path(tools[key]) if key in tools else
              Path('/opt/homebrew/opt/openjdk@25/bin/java') if modern else
              next((self.build/'jdk21').glob('*/Contents/Home/bin/java')))
        jar = next((self.build/self.backend/'target').glob('*.jar'))
        self.native_port = free_port()
        profile = 'dev' if self.backend.startswith('auth-') else 'local'
        cmd = [str(java), '-Xms64m', '-Xmx384m', '-jar', str(jar), '--spring.profiles.active='+profile,
               '--server.address=127.0.0.1', '--server.port='+str(self.native_port),
               '--logging.level.root=WARN', '--logging.level.org.zalando.logbook=OFF',
               '--logging.level.org.springframework.security=WARN', '--spring.jpa.show-sql=false',
               '--spring.activemq.broker-url=tcp://127.0.0.1:1', '--ollama.base-url=http://127.0.0.1:1']
        if modern:
            cmd += ['--app.seed-demo-data.enabled=false', '--app.bootstrap-products.enabled=false',
                    '--app.bootstrap-admin.enabled=true', '--app.bootstrap-admin.username='+ADMIN['username'],
                    '--app.bootstrap-admin.password='+ADMIN['password'], '--app.bootstrap-admin.email=admin@example.test']
        (self.control/'launch.json').write_text(json.dumps({'command': cmd, 'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest()}, indent=2))
        with open(self.control/'native.log', 'w') as log:
            self.proc = subprocess.Popen(cmd, cwd=self.control, stdout=log, stderr=log, start_new_session=True)
        base = 'http://127.0.0.1:'+str(self.native_port)
        route = '/api/v1/users/signin' if modern else '/users/signin'
        for _ in range(180):
            if self.proc.poll() is not None:
                raise RuntimeError('Native startup failed: '+str(self.control/'native.log'))
            try:
                response = request(base+route, 'POST', ADMIN if modern else {'username':'admin','password':'admin'})
                if response['status'] == 200:
                    break
                if not modern and response['status'] in (400, 401, 403):
                    break  # Startup reached application; credentials are supplied separately for legacy cases.
            except (OSError, http.client.HTTPException):
                pass
            time.sleep(.5)
        else:
            raise TimeoutError('Native application never became ready')
        if modern:
            self.seed(base, response['json']['token'])
        elif self.legacy:
            admin={**ADMIN,'email':'adminhistory@example.test','firstName':'Admin','lastName':'Jones','roles':['ROLE_ADMIN','ROLE_CLIENT']}
            assert request(base+'/users/signup','POST',admin)['status']==201
            token=request(base+'/users/signin','POST',ADMIN)['json']['token']
            self.seed(base,token,legacy=True)

    def seed(self, base, admin_token, legacy=False):
        users='/users' if legacy else '/api/v1/users'
        api='/api' if legacy else '/api/v1'
        account = {**CUSTOMER, 'email':'customer@example.test', 'firstName':'Taylor','lastName':'Jones'}
        if legacy:
            account['roles']=['ROLE_CLIENT']
        created = request(base+users+'/signup', 'POST', account)
        assert created['status'] == 201, created
        login = request(base+users+'/signin', 'POST', CUSTOMER)
        assert login['status'] == 200, login
        self.customer_token = login['json']['token']
        products = []
        for name, category in [('Desk lamp','Home'), ('Travel mug','Kitchen'),
                ('ReplacementCartridgeSeriesIndustrialCompatibilityEditionABC123456789','IndustrialReplacementCartridges')]:
            item = request(base+api+'/products', 'POST', {'name':name, 'description':'Replacement and everyday catalog supplies.',
                           'price':49.95, 'stockQuantity':20, 'category':category, 'imageUrl':''}, admin_token)
            assert item['status'] in (200,201), item
            products.append(item['json'])
        self.products = products
        cart = request(base+api+'/cart/items','POST',{'productId':products[0]['id'],'quantity':2}, self.customer_token)
        assert cart['status'] in (200,201), cart
        (self.control/'seed.json').write_text(json.dumps({'account':account,'products':products,'cart':cart},indent=2))

    def stop(self):
        if self.api_server:
            self.api_server.shutdown()
            self.api_server.server_close()
            self.api_server=None
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.stop()
