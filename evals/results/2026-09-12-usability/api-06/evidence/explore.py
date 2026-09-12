import json, urllib.request, urllib.error, time, hashlib
from pathlib import Path
from datetime import datetime, timezone
BASE = 'http://127.0.0.1:49527'
START = time.monotonic()
records = []

def probe(name, payload=None, raw=None, path='/api/v1/users/signin', method='POST', expected=None):
    data = raw if raw is not None else (json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode() if payload is not None else None)
    safe = payload.copy() if isinstance(payload, dict) else payload
    if isinstance(safe, dict) and 'password' in safe:
        val = safe['password']
        if isinstance(val, str):
            safe['password'] = {'placeholder': 'SYNTHETIC_PASSWORD', 'unicode_characters': len(val), 'utf8_bytes': len(val.encode())}
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            status, headers, body = response.status, dict(response.headers), response.read().decode()
    except urllib.error.HTTPError as response:
        status, headers, body = response.code, dict(response.headers), response.read().decode()
    except Exception as e:
        status, headers, body = None, {}, str(e)
    record = {'number': len(records)+1, 'name': name, 'time_utc': datetime.now(timezone.utc).isoformat(), 'method':method, 'path':path, 'request':safe, 'raw_input_description': ('malformed JSON: {' if raw == b'{' else 'raw non-object or byte-sized JSON' if raw is not None else None), 'encoded_bytes':len(data) if data else 0, 'status':status, 'headers':headers, 'body':body, 'elapsed_ms':round((time.monotonic()-started)*1000, 2), 'expected_status':expected, 'status_matches':status==expected if expected else None}
    records.append(record)
    Path('evidence/http.json').write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(record['number'], name, status, body[:180])
    return status

if probe('build availability', method='GET', path='/health', expected=200) != 200:
    raise SystemExit('Runtime unavailable; no further requests attempted')
probe('no record before sign-in', method='GET', path='/api/v1/users/probe_c_0612', expected=404)
probe('valid representative', {'username':'probe_c_0612','password':'Invented_pass_61'}, expected=422)
for field in ('username','password'):
    for length in (3,4,255,256):
        payload={'username':'probe_c_0612','password':'Invented_pass_61'}
        payload[field]=('u' if field=='username' else 'p')*length
        probe(f'{field} ASCII length {length}', payload, expected=422 if 4<=length<=255 else 400)
for length in (3,4,255,256):
    probe(f'password Unicode length {length}', {'username':'probe_c_0612','password':'🔑'*length}, expected=422 if 4<=length<=255 else 400)
for field in ('username','password'):
    for variant in ('missing','null','number'):
        payload={'username':'probe_c_0612','password':'Invented_pass_61'}
        if variant=='missing': del payload[field]
        else: payload[field]=None if variant=='null' else 12345
        probe(f'{field} {variant}', payload, expected=400)
probe('malformed JSON',raw=b'{',expected=400)
probe('non-object JSON array',raw=b'[]',expected=400)
probe('unknown fields ignored', {'username':'probe_c_0612','password':'Invented_pass_61','extra':{'nested':True}},expected=422)
for size in (8192,8193):
    payload={'username':'probe_c_0612','password':'Invented_pass_61','padding':''}
    used=len(json.dumps(payload,separators=(',',':')).encode())
    payload['padding']='x'*(size-used)
    raw=json.dumps(payload,separators=(',',':')).encode()
    probe(f'JSON body size {size}',raw=raw,expected=422 if size==8192 else 413)
probe('repeat username upper boundary',{'username':'u'*256,'password':'Invented_pass_61'},expected=400)
probe('repeat password upper boundary',{'username':'probe_c_0612','password':'p'*256},expected=400)
probe('corrected lengths after upper boundary errors',{'username':'u'*255,'password':'p'*255},expected=422)
probe('no record after sign-in', method='GET', path='/api/v1/users/probe_c_0612', expected=404)
Path('evidence/accounting.json').write_text(json.dumps({'api_requests':len(records),'availability_requests':1,'browser_actions':0,'browser_sessions_created':0,'elapsed_seconds':round(time.monotonic()-START,2)},indent=2))
source = []
for filename in ('app/app.py','app/domain.py'):
    content=Path(filename).read_bytes()
    source.append(filename+' SHA256 '+hashlib.sha256(content).hexdigest()+'\n'+''.join(f'{i}: {line}\n' for i,line in enumerate(content.decode().splitlines(),1)))
Path('evidence/source.txt').write_text('\n'.join(source))
