"""Bounded probes against the assigned runtime. Requires fresh owner-reset fixtures."""
import json, time, urllib.request, urllib.error
from pathlib import Path
BASE = 'http://127.0.0.1:55996'
OUT = Path(__file__).parent
records = []
def request(label, method, path, body=None, actor='alice', raw=None):
    if len(records) >= 100:
        raise RuntimeError('Local request budget exhausted')
    headers = {'Content-Type':'application/json'}
    if actor is not None:
        headers['X-Test-User'] = actor
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    start = time.monotonic()
    try:
        response = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        text = response.read().decode()
        try: result = json.loads(text)
        except ValueError: result = text
        entry = {'n':len(records)+1, 'label':label, 'method':method, 'path':path,
                 'actor':actor, 'body':body if raw is None else raw.decode(),
                 'status':response.status, 'headers':dict(response.headers), 'response':result,
                 'elapsed_ms':round((time.monotonic()-start)*1000,1)}
    records.append(entry)
    (OUT/'http-evidence.json').write_text(json.dumps(records, indent=2)+'\n')
    print(f"{entry['n']:02} {label}: {entry['status']}", flush=True)
    if entry['status'] in (502,503,504):
        raise RuntimeError('Feature unavailable; stopping probes')
    return entry['status'], result

def get(label, actor='alice'):
    return request(label,'GET','/api/orders',actor=actor)[1]['orders']
def post(label,path,body,actor='alice'):
    return request(label,'POST',path,body,actor)

initial = {'alice':get('baseline Alice'), 'bob':get('baseline Bob','bob')}
(OUT/'initial-state.json').write_text(json.dumps(initial,indent=2)+'\n')
assert all(o['refunded'] == 0 and o['version'] == 1 for orders in initial.values() for o in orders), 'Requires fresh owner-reset fixtures; stopping before mutation'
# Boundary contrasts: fixture identity isolation on every administrative operation.
request('anonymous list','GET','/api/orders',actor=None)
request('anonymous write','POST','/api/orders/A200/note',{'note':'unauthorized'},actor=None)
request('Alice reads Bob','GET','/api/orders/B100')
request('Bob reads Alice','GET','/api/orders/A200',actor='bob')
for operation, body in [('refund',{'amount':1}),('address',{'address':'Unauthorized','version':1}),('note',{'note':'Unauthorized'})]:
    post('Alice forbidden '+operation,'/api/orders/B100/'+operation,body)
post('forbidden service first','/api/services',{'ids':['B100','A200'],'service':'express'})
get('Bob unchanged after forbidden writes','bob')
get('Alice unchanged after forbidden-first batch')
# Valid refund, cumulative exact boundary, then a single cent beyond remaining.
post('refund valid partial','/api/orders/A200/refund',{'amount':1000})
post('refund cumulative exact payment','/api/orders/A200/refund',{'amount':5000})
get('refund at exact boundary')
post('refund exceeds cumulative by one cent','/api/orders/A200/refund',{'amount':1})
get('refund overpayment persisted')
post('refund single amount exceeds original','/api/orders/A200/refund',{'amount':6001})
for amount in [0,-1,True,1.5,'1',None]:
    post('refund invalid '+repr(amount),'/api/orders/A200/refund',{'amount':amount})
get('refund rejects preserve state')
# Version conflict: two edits based on the same customer read.
v = initial['alice'][0]['version']
post('address valid current version','/api/orders/A100/address',{'address':'Current session address','version':v})
post('address stale version','/api/orders/A100/address',{'address':'Stale session overwrote newer','version':v})
state = get('stale address persisted')
current = next(x for x in state if x['id']=='A100')
post('address future version','/api/orders/A100/address',{'address':'Future version','version':current['version']+1})
for body in [{'address':'   ','version':current['version']},{'address':'x'*121,'version':current['version']},{'address':'Valid','version':True}]:
    post('address invalid shape','/api/orders/A100/address',body)
get('address rejected controls preserve state')
post('restore address','/api/orders/A100/address',{'address':initial['alice'][0]['address'],'version':current['version']})
# Atomicity failure on both missing and forbidden trailing IDs, fresh service baseline each time.
for target in ['MISSING','B100']:
    get('batch before '+target)
    post('batch valid then '+target,'/api/services',{'ids':['A100',target],'service':'express'})
    get('batch after '+target)
    if target=='B100': get('forbidden order unchanged','bob')
    post('restore service after '+target,'/api/services',{'ids':['A100'],'service':'standard'})
post('valid two-order service','/api/services',{'ids':['A100','A200'],'service':'express'})
get('valid batch persisted')
post('restore both services','/api/services',{'ids':['A100','A200'],'service':'standard'})
for body in [{'ids':[],'service':'express'},{'ids':['A100'],'service':'premium'},{'ids':['A100',2],'service':'express'}]:
    post('service invalid shape','/api/services',body)
# Note success, unsupported operation and malformed request persistence controls.
post('note valid','/api/orders/A200/note',{'note':'Assessment note'})
get('note valid persisted')
post('note unsupported locker','/api/orders/A200/note',{'note':'LOCKER: 1'})
get('note unsupported preserves previous')
for note in ['', '   ', 'x'*161, None]:
    post('note invalid shape','/api/orders/A200/note',{'note':note})
request('malformed JSON','POST','/api/orders/A200/note',raw=b'{')
request('non-object JSON','POST','/api/orders/A200/note',raw=b'[]')
get('note invalid preserves previous')
post('restore note','/api/orders/A200/note',{'note':initial['alice'][1]['note']})
final = {'alice':get('final Alice'), 'bob':get('final Bob','bob')}
(OUT/'final-state.json').write_text(json.dumps(final,indent=2)+'\n')
print('Requests:',len(records))
