import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

base = 'http://127.0.0.1:57088'
events = []
def request(path, actor='alice', data=None):
    headers = {'Content-Type': 'application/json'}
    if actor:
        headers['X-Test-User'] = actor
    req = urllib.request.Request(base + path, headers=headers,
        data=None if data is None else json.dumps(data).encode())
    try:
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as error:
        response = error
    body = json.load(response)
    events.append(dict(path=path, actor=actor, request=data, status=response.status, response=body))
    return response.status, body

before = request('/api/orders')[1]
bob = request('/api/orders', 'bob')[1]
assert request('/api/orders', None)[0] == 401
assert request('/api/orders/B100')[0] == 403
assert request('/api/orders/B100/note', data={'note':'Forbidden journey 09'})[0] == 403
assert request('/api/services', data={'ids':['A100','B100'],'service':'express'})[0] == 403
assert request('/api/orders')[1] == before
assert request('/api/orders','bob')[1] == bob

# Restore only reversible fixture fields touched by browser exploration.
baseline = json.loads(Path('evidence/baseline-alice.json').read_text())
for row in baseline['orders']:
    assert request('/api/orders/'+row['id']+'/note',data={'note':row['note']})[0] == 200
    assert request('/api/services',data={'ids':[row['id']],'service':row['service']})[0] == 200
assert request('/api/orders')[1] == baseline
Path('evidence/api-checks-cleanup.json').write_text(json.dumps(events,indent=2))

hashes = []
for route, local in [('/','index.html'),('/app.js','app.js'),('/style.css','style.css')]:
    with urllib.request.urlopen(base+route) as response:
        deployed = response.read()
    supplied = Path('app/static',local).read_bytes()
    hashes.append(dict(file=local, source_sha256=hashlib.sha256(supplied).hexdigest(),
        deployed_sha256=hashlib.sha256(deployed).hexdigest(),match=supplied==deployed))
Path('evidence/build-match.json').write_text(json.dumps(hashes,indent=2))
print('Backing-call boundaries passed; Alice baseline fully restored; Bob unchanged. API requests:',len(events))
