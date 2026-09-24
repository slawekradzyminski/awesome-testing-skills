import concurrent.futures
import json
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = 'http://127.0.0.1:57593'
OUT = Path(__file__).resolve().parent
records, checks = [], []
mutex = threading.Lock()
count = 1  # Includes the preliminary curl GET /api/orders.

def request(label, method, path, actor='alice', body=None, raw=None):
    global count
    with mutex:
        count += 1
        n = count
        if n > 115:
            raise RuntimeError('Request budget reserved for cleanup')
    headers = {'Content-Type': 'application/json'}
    if actor is not None:
        headers['X-Test-User'] = actor
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    start = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, headers=headers, method=method), timeout=5) as response:
            status, content = response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        status, content = error.code, error.read().decode()
    except Exception as error:
        status, content = 'TRANSPORT_ERROR', repr(error)
    try:
        value = json.loads(content)
    except ValueError:
        value = content
    record = dict(number=n, label=label, method=method, path=path, actor=actor,
                  request=body if raw is None else repr(raw), status=status, response=value,
                  elapsed_ms=round((time.time()-start)*1000))
    with mutex:
        records.append(record)
        with (OUT / 'http.jsonl').open('a') as f:
            f.write(json.dumps(record) + '\n')
    return status, value

def check(label, condition, detail=None):
    checks.append(dict(label=label, passed=bool(condition), detail=detail))
    print(('PASS ' if condition else 'FAIL ') + label, flush=True)

def post(label, path, body, expected, actor='alice'):
    result = request(label, 'POST', path, actor, body)
    check(label, result[0] == expected, result)
    return result

def snapshot(label):
    rows = {}
    for actor in ('alice', 'bob'):
        status, result = request(label + ' ' + actor, 'GET', '/api/orders', actor)
        check(label + ' list ' + actor, status == 200 and all(o['owner'] == actor for o in result['orders']))
        rows.update({o['id']:o for o in result['orders']})
    return rows

(OUT / 'http.jsonl').write_text('')
baseline = snapshot('baseline')
(OUT / 'baseline.json').write_text(json.dumps(baseline, indent=2))
for actor in (None, 'unknown'):
    for method, path, body in [('GET','/api/orders',None), ('GET','/api/orders/A200',None),
        ('POST','/api/orders/A200/refund',{'amount':1}), ('POST','/api/orders/A200/address',{'address':'Unauthorized','version':1}),
        ('POST','/api/orders/A200/note',{'note':'Unauthorized'}), ('POST','/api/services',{'ids':['A200'],'service':'express'})]:
        status, result = request('unauthenticated ' + str(actor), method, path, actor, body)
        check('reject unauthenticated ' + str(actor) + ' ' + path, status == 401)
for actor, target in [('alice','B100'), ('bob','A200')]:
    status, _ = request('foreign read', 'GET', '/api/orders/' + target, actor)
    check('foreign read ' + actor, status == 403)
    for operation, body in [('refund',{'amount':1}),('address',{'address':'Forbidden','version':1}),('note',{'note':'Forbidden'})]:
        post('foreign ' + operation + ' ' + actor, '/api/orders/' + target + '/' + operation, body, 403, actor)
    post('foreign service ' + actor, '/api/services', {'ids':[target],'service':'express'}, 403, actor)
check('authorization attempts preserve all state', snapshot('after authorization') == baseline)

# Batch failures must preserve earlier valid rows as well as forbidden rows.
for ids, expected in [(['A100','B100'],403),(['A100','MISSING'],404),(['B100','A100'],403),(['MISSING','A100'],404)]:
    post('atomic batch ' + str(ids), '/api/services', {'ids':ids,'service':'express'}, expected)
    check('atomic rejection preserves Alice orders ' + str(ids), request('batch state','GET','/api/orders')[1]['orders'] == [baseline['A100'],baseline['A200']])
post('valid two-order batch','/api/services',{'ids':['A100','A200'],'service':'express'},200)
check('batch persisted', all(o['service']=='express' for o in request('batch persisted read','GET','/api/orders')[1]['orders']))
post('restore service','/api/services',{'ids':['A100','A200'],'service':'standard'},200)
for body in [{'ids':[],'service':'express'},{'ids':['A200',42],'service':'express'}, {'ids':'A200','service':'express'}, {'ids':['A200'],'service':'overnight'}]:
    post('invalid batch ' + str(body),'/api/services',body,400)

for amount in [0,-1,True,1.5,'100',None]:
    post('invalid refund ' + str(amount),'/api/orders/A100/refund',{'amount':amount},400)
post('partial refund one','/api/orders/A100/refund',{'amount':3000},200)
post('partial refund two','/api/orders/A100/refund',{'amount':2000},200)
post('cumulative excess','/api/orders/A100/refund',{'amount':5001},409)
check('excess preserves cumulative total',request('refund after excess','GET','/api/orders/A100')[1]['refunded']==5000)
# Two simultaneous refunds would each fit alone, but cannot both fit.
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(request,'concurrent refund '+str(i),'POST','/api/orders/A100/refund','alice',{'amount':3000}) for i in range(2)]
    results=[f.result() for f in futures]
check('concurrent refund one winner', sorted(r[0] for r in results)==[200,409],results)
post('exact remaining refund','/api/orders/A100/refund',{'amount':2000},200)
post('refund exhausted balance','/api/orders/A100/refund',{'amount':1},409)
check('refund final total equals paid',request('refund final read','GET','/api/orders/A100')[1]['refunded']==10000)

for body in [{'address':' ','version':1},{'address':'x'*121,'version':1},{'address':7,'version':1},{'address':'Valid','version':True},{'address':'Valid','version':1.0},{'address':'Valid'}]:
    post('invalid address ' + str(body),'/api/orders/A200/address',body,400)
post('address 120 character boundary','/api/orders/A200/address',{'address':'x'*120,'version':1},200)
post('stale address','/api/orders/A200/address',{'address':'Stale overwrite','version':1},409)
row=request('address after stale','GET','/api/orders/A200')[1]
check('stale preserves new address and version',row['address']=='x'*120 and row['version']==2)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(request,'concurrent address '+str(i),'POST','/api/orders/A200/address','alice',{'address':'Concurrent '+str(i),'version':2}) for i in range(2)]
    results=[f.result() for f in futures]
check('concurrent address one winner',sorted(r[0] for r in results)==[200,409],results)
row=request('address concurrency read','GET','/api/orders/A200')[1]
check('concurrent address preserves winning value',row['version']==3 and row['address']==next(r[1]['address'] for r in results if r[0]==200))
post('restore address','/api/orders/A200/address',{'address':baseline['A200']['address'],'version':row['version']},200)

post('note maximum boundary','/api/orders/A200/note',{'note':'n'*160},200)
for body, expected in [({'note':''},400),({'note':'   '},400),({'note':'n'*161},400),({'note':True},400),({'note':'LOCKER: 1'},422),({'note':'  locker: 2'},422)]:
    post('invalid note '+str(body),'/api/orders/A200/note',body,expected)
check('rejected notes preserve previous value',request('note after rejection','GET','/api/orders/A200')[1]['note']=='n'*160)
post('restore note','/api/orders/A200/note',{'note':baseline['A200']['note']},200)

for raw in [b'{',b'[]',b'null',b'"text"',b'{"note":"\xff"}',b'{}'+b' '*8191]:
    status, value=request('malformed JSON envelope','POST','/api/orders/A200/note',raw=raw)
    check('malformed envelope returns 400 '+repr(raw[:30]), status==400)
post('missing order refund','/api/orders/MISSING/refund',{'amount':1},404)
post('missing order address','/api/orders/MISSING/address',{'address':'Test','version':1},404)
post('missing order note','/api/orders/MISSING/note',{'note':'Test'},404)
final=snapshot('final')
(OUT / 'final-state.json').write_text(json.dumps(final,indent=2))
expected=json.loads(json.dumps(baseline))
expected['A100']['refunded']=10000
expected['A200']['version']=4
check('cleanup matches expected irreversible counters only',final==expected,final)
summary=dict(api_requests_including_preliminary=count,checks=len(checks),passed=sum(c['passed'] for c in checks),failed=[c for c in checks if not c['passed']],results=checks)
(OUT / 'checks.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))
