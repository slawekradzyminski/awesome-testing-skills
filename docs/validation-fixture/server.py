from http.server import BaseHTTPRequestHandler, HTTPServer
import json
state = {"displayName": "Original", "saveCount": 0}
orders = {"1": {"id": "1", "owner": "alice", "item": "Book"}, "2": {"id": "2", "owner": "bob", "item": "Pen"}}
html = """<!doctype html><html lang="en"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Profile test fixture</title>
<style>body{font:18px system-ui;max-width:480px;margin:40px auto;padding:20px}input,button{font:inherit;padding:10px;margin:8px 0}label{display:block}</style>
<h1>Profile settings</h1><form id="profile"><label for="name">Display name</label><input id="name" name="name" required value="Original"><div><button type="submit">Save</button> <button id="cancel">Cancel</button></div></form><p id="status" role="status"></p>
<script>document.querySelector('#profile').addEventListener('submit',async e=>{e.preventDefault();await fetch('/api/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({displayName:document.querySelector('#name').value})});document.querySelector('#status').textContent='Saved';});document.querySelector('#cancel').addEventListener('click',()=>{document.querySelector('#status').textContent='Cancelled';});</script></html>"""
class Handler(BaseHTTPRequestHandler):
 def reply(self, code, value):
  body=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_GET(self):
  if self.path == '/':
   body=html.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body)
  elif self.path == '/api/profile': self.reply(200,state)
  elif self.path.startswith('/api/orders/'):
   who=self.headers.get('X-Test-User')
   if who not in ('alice','bob'): self.reply(401,{'error':'Authentication required'})
   else:
    order=orders.get(self.path.rsplit('/',1)[-1])
    self.reply(200,order) if order else self.reply(404,{'error':'Not found'})
  else:self.reply(404,{'error':'Not found'})
 def do_POST(self):
  if self.path != '/api/profile': self.reply(404,{});return
  payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  state['displayName']=payload['displayName'];state['saveCount']+=1;self.reply(200,state)
server=HTTPServer(('127.0.0.1',0),Handler)
print(server.server_port,flush=True)
server.serve_forever()
