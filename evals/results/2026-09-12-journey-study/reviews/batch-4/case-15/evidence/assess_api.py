import concurrent.futures as futures
import json
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = 'http://127.0.0.1:57710'
OUT = Path(__file__).resolve().parent
lock = threading.Lock()
records, checks = [], []
count = 0

def check(label, condition, detail=None):
    checks.append({'check': label, 'pass': bool(condition), 'detail': detail})

def req(label, method, path, body=None, actor='alice', expected=200, raw=None):
    global count
    with lock:
        count += 1
        n = count
    if n > 118:
        raise RuntimeError('Request budget reached')
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers = {'Content-Type': 'application/json'}
    if actor is not None:
        headers['X-Test-User'] = actor
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            status, text = response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        status, text = error.code, error.read().decode()
    except Exception as error:
        status, text = 0, repr(error)
    try:
        result = json.loads(text)
    except ValueError:
        result = text
    record = {'request': n, 'label': label, 'method': method, 'path': path, 'actor': actor,
              'body': body, 'raw_hex': raw.hex() if raw is not None else None,
              'status': status, 'response': result, 'elapsed_ms': round((time.time()-started)*1000)}
    with lock:
        records.append(record)
        with (OUT / 'http.jsonl').open('a') as file:
            file.write(json.dumps(record) + '\n')
    if expected is not None:
        check(label + ': status', status == expected, {'expected': expected, 'actual': status, 'request': n})
    return status, result

def snapshot(label):
    rows = {}
    for actor in ['alice', 'bob']:
        _, data = req(label + ' ' + actor, 'GET', '/api/orders', actor=actor)
        rows.update({row['id']: row for row in data['orders']})
    return rows

def post(label, oid, operation, body, expected=200, actor='alice'):
    return req(label, 'POST', f'/api/orders/{oid}/{operation}', body, actor, expected)

(OUT / 'http.jsonl').write_text('')
before = snapshot('baseline')
(OUT / 'baseline.json').write_text(json.dumps(before, indent=2))
check('Alice list is isolated', {k for k,v in before.items() if v['owner']=='alice'} == {'A100','A200'})
check('Bob list is isolated', {k for k,v in before.items() if v['owner']=='bob'} == {'B100'})
for actor, expected_ids in [('alice', {'A100','A200'}), ('bob', {'B100'})]:
    rows = next(r['response']['orders'] for r in records if r['label']=='baseline '+actor)
    check(actor+' actual list contains only own orders', {r['id'] for r in rows} == expected_ids)
req('owner detail', 'GET', '/api/orders/A100')
req('other owner detail', 'GET', '/api/orders/B100', actor='bob')
for actor in [None, 'unknown']:
    req('unauthenticated list '+str(actor), 'GET', '/api/orders', actor=actor, expected=401)
    req('unauthenticated detail '+str(actor), 'GET', '/api/orders/A100', actor=actor, expected=401)
    for operation, body in [('refund', {'amount':1}), ('address', {'address':'Unauthorized','version':1}), ('note', {'note':'Unauthorized'})]:
        post('unauthenticated '+operation+' '+str(actor), 'A100', operation, body, 401, actor)
    req('unauthenticated services '+str(actor), 'POST', '/api/services', {'ids':['A100'],'service':'express'}, actor, 401)
for actor, oid in [('alice','B100'),('bob','A100')]:
    req('foreign detail '+actor, 'GET', '/api/orders/'+oid, actor=actor, expected=403)
    for operation, body in [('refund', {'amount':1}),('address',{'address':'Unauthorized','version':1}),('note',{'note':'Unauthorized'})]:
        post('foreign '+operation+' '+actor, oid, operation, body, 403, actor)
    req('foreign service '+actor, 'POST', '/api/services', {'ids':[oid],'service':'express'}, actor, 403)
req('missing detail', 'GET', '/api/orders/MISSING', expected=404)
for operation, body in [('refund', {'amount':1}),('address', {'address':'Missing','version':1}),('note',{'note':'Missing'})]:
    post('missing '+operation, 'MISSING', operation, body, 404)
check('Access failures preserve all fixture state', snapshot('after access failures') == before)

for amount in [0, -1, 1.5, True, '100', None]:
    post('invalid refund '+repr(amount), 'A100', 'refund', {'amount':amount}, 400)
for body in [{}, {'address':'   ','version':1}, {'address':'x'*121,'version':1}, {'address':5,'version':1}, {'address':'Valid','version':True}, {'address':'Valid','version':'1'}, {'address':'Valid','version':1.0}]:
    post('invalid address '+repr(body), 'A100', 'address', body, 400)
for body in [{'note':''}, {'note':' \t\n'}, {'note':'x'*161}, {'note':True}, {}]:
    post('invalid note '+repr(body), 'A100', 'note', body, 400)
for body in [{'ids':[],'service':'express'}, {'ids':'A100','service':'express'}, {'ids':['A100',3],'service':'express'}, {'ids':['A100'],'service':'overnight'}, {}]:
    req('invalid services '+repr(body), 'POST', '/api/services', body, expected=400)
for raw in [b'{', b'[]', b'null', b'42', b'', b'{"note":"\xff"}', b' '*8193]:
    req('invalid JSON envelope '+str(len(raw))+' bytes '+raw[:15].hex(), 'POST', '/api/orders/A100/note', expected=400, raw=raw)
check('Malformed input preserves all state', snapshot('after invalid inputs') == before)

for oid in ['A100','A200']:
    req('mixed forbidden batch '+oid, 'POST', '/api/services', {'ids':[oid,'B100'],'service':'express'}, expected=403)
req('mixed missing batch', 'POST', '/api/services', {'ids':['A100','MISSING'],'service':'express'}, expected=404)
check('Failed batches are atomic', snapshot('after failed batches') == before)
_, batch = req('valid batch', 'POST', '/api/services', {'ids':['A100','A200'],'service':'express'})
check('Both service changes returned', len(batch['orders'])==2 and all(o['service']=='express' for o in batch['orders']))
_, listed = req('persisted service batch', 'GET', '/api/orders')
check('Both service changes persist', all(o['service']=='express' for o in listed['orders']))
for length in [1,160]:
    _, row = post('note boundary '+str(length), 'A100', 'note', {'note':'N'*length})
    check('note boundary saved '+str(length), row.get('note')=='N'*length)
for note in ['LOCKER: 1','  locker: 2']:
    post('unsupported note '+note, 'A100','note',{'note':note},422)
_, row = req('note after rejections','GET','/api/orders/A100')
check('Rejected notes preserve prior saved note', row['note']=='N'*160)
version = before['A100']['version']
_, row = post('address max length', 'A100', 'address', {'address':'A'*120,'version':version})
check('Address save increments version', row['version']==version+1 and row['address']=='A'*120)
post('stale address', 'A100','address',{'address':'Stale overwrite','version':version},409)
_, row = req('address after stale save','GET','/api/orders/A100')
check('Stale address preserves newer value', row['address']=='A'*120 and row['version']==version+1)
barrier = threading.Barrier(2)
def race_address(address):
    barrier.wait()
    return post('concurrent address '+address,'A100','address',{'address':address,'version':version+1},None)
with futures.ThreadPoolExecutor(max_workers=2) as pool:
    outcomes = list(pool.map(race_address,['Concurrent one','Concurrent two']))
check('Exactly one competing address accepted', sorted(s for s,_ in outcomes)==[200,409])
winner = next((r for s,r in outcomes if s==200), {})
_, row = req('address after race','GET','/api/orders/A100')
check('Concurrent winning address persists with single increment', row==winner and row['version']==version+2)

initial = before['A100']['refunded']
for amount in [1000,2000]:
    _, row = post('partial refund '+str(amount),'A100','refund',{'amount':amount})
check('Partial refunds accumulate', row['refunded']==initial+3000)
remaining = before['A100']['paid'] - initial - 3000
post('excess cumulative refund','A100','refund',{'amount':remaining+1},409)
_, row = req('refund after excessive request','GET','/api/orders/A100')
check('Excessive refund records nothing', row['refunded']==initial+3000)
_, row = post('exact remaining refund','A100','refund',{'amount':remaining})
check('Exact remaining refund reaches payment',row['refunded']==row['paid'])
post('refund after exhaustion','A100','refund',{'amount':1},409)
barrier = threading.Barrier(2)
def race_refund(index):
    barrier.wait()
    return post('concurrent refund '+str(index),'A200','refund',{'amount':4000},None)
with futures.ThreadPoolExecutor(max_workers=2) as pool:
    outcomes = list(pool.map(race_refund,[1,2]))
check('Exactly one competing refund accepted',sorted(s for s,_ in outcomes)==[200,409])
_, row = req('refund after race','GET','/api/orders/A200')
check('Concurrent refunds cannot exceed payment',row['refunded']==before['A200']['refunded']+4000 and row['refunded']<=row['paid'])

# Restore reversible fields. Version counters and refunds must remain disclosed.
post('restore original note','A100','note',{'note':before['A100']['note']})
post('restore original address','A100','address',{'address':before['A100']['address'],'version':version+2})
for oid in ['A100','A200']:
    req('restore service '+oid,'POST','/api/services',{'ids':[oid],'service':before[oid]['service']})
after = snapshot('final state')
for oid, original in before.items():
    check('Restored reversible fields '+oid,all(after[oid][field]==original[field] for field in ['address','note','service']))
check('Bob remains completely unchanged',after['B100']==before['B100'])
(OUT/'final-state.json').write_text(json.dumps(after,indent=2))
summary = {'api_requests':count,'checks':len(checks),'passed':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']], 'results':checks}
(OUT/'results.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))
