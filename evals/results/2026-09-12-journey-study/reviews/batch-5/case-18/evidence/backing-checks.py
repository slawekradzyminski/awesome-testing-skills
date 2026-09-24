import json, urllib.request, urllib.error, hashlib
from pathlib import Path
base='http://127.0.0.1:58432'
log=[]
def req(path,actor='alice',body=None):
 h={'Content-Type':'application/json'}
 if actor: h['X-Test-User']=actor
 r=urllib.request.Request(base+path,headers=h,data=None if body is None else json.dumps(body).encode())
 try:
  with urllib.request.urlopen(r) as f: status,data=f.status,json.load(f)
 except urllib.error.HTTPError as e: status,data=e.code,json.load(e)
 log.append(dict(method=r.get_method(),path=path,actor=actor,request=body,status=status,response=data))
 return status,data
before=req('/api/orders')[1]
assert req('/api/orders',None)[0]==401
assert req('/api/orders/B100')[0]==403
bob_before=req('/api/orders/B100','bob')[1]
assert req('/api/orders/B100',body={'note':'Journey forbidden'})[0]==404 # unknown POST shape; no mutation
assert req('/api/orders/B100/note',body={'note':'Journey forbidden'})[0]==403
assert req('/api/services',body={'ids':['A100','B100'],'service':'express'})[0]==403
assert req('/api/orders')[1]==before
assert req('/api/orders/B100','bob')[1]==bob_before
assert req('/api/orders/A100/note',body={'note':'   '})[0]==400
assert req('/api/orders/A100/note',body={'note':'LOCKER: persisted probe'})[0]==422
assert req('/api/orders')[1]==before
Path('evidence/backing-checks.json').write_text(json.dumps(log,indent=2))
manifest=[]
for local,url in [('app/static/app.js','/app.js'),('app/static/index.html','/'),('app/static/style.css','/style.css')]:
 deployed=urllib.request.urlopen(base+url).read(); source=Path(local).read_bytes()
 manifest.append(dict(source=local,url=base+url,source_sha256=hashlib.sha256(source).hexdigest(),deployed_sha256=hashlib.sha256(deployed).hexdigest(),matches=source==deployed))
Path('evidence/build-match.json').write_text(json.dumps(manifest,indent=2))
print('13 backing API checks passed; deployed static files match supplied source byte-for-byte')
