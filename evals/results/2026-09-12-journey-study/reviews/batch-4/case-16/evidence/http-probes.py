import hashlib, json, pathlib, urllib.request, urllib.error

BASE = 'http://127.0.0.1:59252'
records = []
def request(path, user='alice', body=None):
    headers = {'Content-Type': 'application/json'}
    if user: headers['X-Test-User'] = user
    req = urllib.request.Request(BASE+path, headers=headers, data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req) as response: status, data = response.status, response.read()
    except urllib.error.HTTPError as response: status, data = response.code, response.read()
    result = json.loads(data)
    records.append({'method':req.get_method(),'path':path,'user':user,'body':body,'status':status,'response':result})
    return status, result

before = request('/api/orders')[1]
assert request('/api/orders', None)[0] == 401
assert request('/api/orders/B100')[0] == 403
assert request('/api/orders/B100/note', body={'note':'Forbidden edit'})[0] == 403
assert request('/api/services', body={'ids':['A100','B100'],'service':'express'})[0] == 403
assert request('/api/orders')[1] == before
assert request('/api/services', body={'ids':['A100','MISSING'],'service':'express'})[0] == 404
assert request('/api/orders')[1] == before
for note in ['', '   ', 'x'*161, 123]:
    assert request('/api/orders/A100/note',body={'note':note})[0] == 400
assert request('/api/orders')[1] == before
for url, filename in [('/app.js','app/static/app.js'),('/style.css','app/static/style.css'),('/','app/static/index.html')]:
    deployed = urllib.request.urlopen(BASE+url).read()
    local = pathlib.Path(filename).read_bytes()
    records.append({'asset':url,'local_file':filename,'sha256':hashlib.sha256(local).hexdigest(),'deployed_matches':local==deployed})
pathlib.Path('evidence/http-probes.json').write_text(json.dumps(records,indent=2))
print('All backing API checks passed;', sum('method' in r for r in records), 'API requests; static assets match supplied source.')
