import json, urllib.request, urllib.error, time, hashlib
from pathlib import Path
from datetime import datetime, timezone
BASE='http://127.0.0.1:49531'
root=Path('.')
records=[]
started=datetime.now(timezone.utc).isoformat()
def send(name, body=None, expected=422, field=None, raw=None, method='POST', path='/api/v1/users/signin', note=None):
    data=raw if raw is not None else (json.dumps(body,ensure_ascii=False).encode() if body is not None else None)
    req=urllib.request.Request(BASE+path,data=data,method=method,headers={'Content-Type':'application/json'} if data is not None else {})
    t=time.monotonic()
    try:
        with urllib.request.urlopen(req,timeout=3) as r: status,headers,response=r.status,dict(r.headers),r.read().decode()
    except urllib.error.HTTPError as e: status,headers,response=e.code,dict(e.headers),e.read().decode()
    except Exception as e: status,headers,response=None,{},str(e)
    try: result=json.loads(response)
    except Exception: result=response
    safe={}
    if isinstance(body,dict):
        for k,v in body.items():
            safe[k]=({'type':'synthetic string','characters':len(v),'utf8_bytes':len(v.encode()),'value':'<invented password omitted>'} if k=='password' and isinstance(v,str) else v)
    else: safe=body
    ok=status==expected
    if expected==422: ok=ok and result=={'message':'Invalid username/password supplied'}
    if field: ok=ok and isinstance(result,dict) and field in result and '4' in result[field] and '255' in result[field]
    rec={'id':len(records)+1,'name':name,'method':method,'path':path,'input':safe if raw is None else note,'request_bytes':len(data) if data else 0,'status':status,'headers':headers,'body':result,'elapsed_ms':round((time.monotonic()-t)*1000,2),'expected_status':expected,'passed':ok}
    records.append(rec)
    Path('evidence/http.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    print(f'{rec["id"]}: {name}: {status} {"PASS" if ok else "FAIL"}')
    return status
status=send('Runtime availability and advertised build',method='GET',path='/health',expected=200)
if status is not None:
    valid={'username':'probe_signin_g','password':'Invented_42'}
    send('Representative length-valid credentials',valid)
    for field in ('username','password'):
        for length in (0,3,4,255,256):
            body=dict(valid);body[field]=('u' if field=='username' else 'p')*length
            send(f'{field} ASCII length {length}',body,422 if 4<=length<=255 else 400,None if 4<=length<=255 else field)
        for label,value in [('null',None),('integer',42),('boolean',True),('array',[]),('object',{})]:
            body=dict(valid);body[field]=value
            send(f'{field} wrong type {label}',body,400,field)
        body=dict(valid);del body[field]
        send(f'{field} missing',body,400,field)
    for length in (3,4,255,256):
        body=dict(valid);body['password']='🔒'*length
        send(f'Unicode password {length} codepoints',body,422 if 4<=length<=255 else 400,None if 4<=length<=255 else 'password')
    send('Both fields invalid: first corrective step',{'username':'abc','password':'xyz'},400,'username')
    send('Correct username: next field guidance',{'username':'abcd','password':'xyz'},400,'password')
    send('Correct both fields: credential feedback',{'username':'abcd','password':'xyzz'})
    send('Ignored extra fields',dict(valid,email='example@synthetic.test',admin=True))
    for label,raw in [('malformed JSON',b'{'),('array body',b'[]'),('null body',b'null'),('string body',b'"example"')]:
        send(label,expected=400,raw=raw,note=raw.decode())
    send('Empty object',{},400,'username')
    for size,expected in [(8192,422),(8193,413)]:
        raw=json.dumps(dict(valid,ignored='')).encode()
        raw=raw[:-2]+b'x'*(size-len(raw))+raw[-2:]
        send(f'Encoded body {size} bytes',expected=expected,raw=raw,note=f'Valid synthetic credentials plus ignored ASCII padding; exactly {size} encoded bytes; credentials omitted')
meta={'started':started,'ended':datetime.now(timezone.utc).isoformat(),'request_count':len(records),'availability_requests':1,'browser_actions':0,'source_files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('app/app.py'),Path('app/domain.py'),Path('requirements.md')]}}
Path('evidence/session.json').write_text(json.dumps(meta,indent=2))
