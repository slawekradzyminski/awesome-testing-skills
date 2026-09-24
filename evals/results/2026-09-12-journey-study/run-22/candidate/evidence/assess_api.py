import json, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = 'http://127.0.0.1:59591'
OUT = Path(__file__).parent
logs, checks = [], []
mutex = threading.Lock()
count = 0

def call(label, method='GET', path='/api/orders', actor='alice', body=None, raw=None):
    global count
    with mutex:
        count += 1
        n = count
        if n > 115: raise RuntimeError('Request budget reached')
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers = {'Content-Type': 'application/json'}
    if actor is not None: headers['X-Test-User'] = actor
    req = Request(BASE + path, data=data, headers=headers, method=method)
    start = time.monotonic()
    try:
        with urlopen(req, timeout=5) as response:
            status, payload = response.status, response.read().decode()
    except HTTPError as error:
        status, payload = error.code, error.read().decode()
    except Exception as error:
        status, payload = 0, repr(error)
    try: value = json.loads(payload)
    except ValueError: value = payload
    entry = dict(n=n, label=label, method=method, path=path, actor=actor,
                 request=body if raw is None else repr(raw), status=status, response=value,
                 seconds=round(time.monotonic()-start, 3))
    with mutex:
        logs.append(entry)
        with (OUT/'http.jsonl').open('a') as f: f.write(json.dumps(entry)+'\n')
    return status, value

def check(label, actual, expected):
    checks.append(dict(label=label, passed=actual==expected, actual=actual, expected=expected))

def post(label, oid, op, body, expected, actor='alice'):
    status, value = call(label, 'POST', '/api/orders/'+oid+'/'+op, actor, body)
    check(label, status, expected)
    return value

def service(label, body, expected, actor='alice'):
    status, value = call(label, 'POST', '/api/services', actor, body)
    check(label, status, expected)
    return value

def snapshot(label):
    result = {}
    for actor in ('alice', 'bob'):
        status, value = call(label+' '+actor, actor=actor)
        check(label+' list '+actor, status, 200)
        for row in value['orders']: result[row['id']] = row
    return result

(OUT/'http.jsonl').write_text('')
initial = snapshot('baseline')
(OUT/'initial-state.json').write_text(json.dumps(initial, indent=2)+'\n')
check('Alice sees only own orders', sorted(k for k,v in initial.items() if v['owner']=='alice'), ['A100','A200'])
check('Bob sees only own orders', sorted(k for k,v in initial.items() if v['owner']=='bob'), ['B100'])
for actor in (None, 'mallory'):
    for method, path, body in [('GET','/api/orders',None),('GET','/api/orders/A200',None),('POST','/api/orders/A200/refund',{'amount':1}),('POST','/api/services',{'ids':['A200'],'service':'express'})]:
        check('unauthorized '+str(actor)+' '+path+' '+method, call('unauthorized',method,path,actor,body)[0],401)
for actor, oid in [('alice','B100'),('bob','A200')]:
    check('cross owner read '+actor, call('cross owner read','GET','/api/orders/'+oid,actor)[0],403)
    for op, body in [('refund',{'amount':1}),('address',{'address':'Forbidden','version':1}),('note',{'note':'Forbidden'})]:
        post('cross owner '+actor+' '+op,oid,op,body,403,actor)
    service('cross owner '+actor+' service',{'ids':[oid],'service':'express'},403,actor)
for op, body in [('refund',{'amount':1}),('address',{'address':'Missing','version':1}),('note',{'note':'Missing'})]:
    post('missing '+op,'NO_SUCH_ORDER',op,body,404)
check('missing read',call('missing read','GET','/api/orders/NO_SUCH_ORDER')[0],404)
for raw in (b'{',b'[]',b'null',b'1',b'"x"',b'',b'{"note":"'+b'x'*8200+b'"}'):
    check('malformed object '+str(len(raw)),call('malformed JSON','POST','/api/orders/A200/note',raw=raw)[0],400)
for amount in (None,True,False,0,-1,1.5,'1',[],{}):
    post('invalid refund '+repr(amount),'A200','refund',{'amount':amount},400)
for body in ({},{'address':'','version':1},{'address':' \n ','version':1},{'address':'x'*121,'version':1},{'address':22,'version':1},{'address':'x','version':True},{'address':'x','version':1.0},{'address':'x','version':'1'}):
    post('invalid address '+repr(body),'A200','address',body,400)
for note in (None,'','  ','x'*161,22):
    post('invalid note '+repr(note),'A200','note',{'note':note},400)
for body in ({},{'ids':[],'service':'express'},{'ids':'A200','service':'express'},{'ids':[1],'service':'express'},{'ids':['A200'],'service':'overnight'},{'ids':['A200'],'service':None}):
    service('invalid services '+repr(body),body,400)
unchanged = snapshot('after rejection checks')
check('all rejection probes preserve all state',unchanged,initial)
# A valid order before an invalid one catches partial application.
for bad, expected in [('NO_SUCH_ORDER',404),('B100',403)]:
    service('batch atomicity '+bad,{'ids':['A100',bad,'A200'],'service':'express'},expected)
state = snapshot('after rejected batches')
check('failed batches preserve every order',state,initial)
service('valid two order batch',{'ids':['A100','A200'],'service':'express'},200)
state = snapshot('after successful batch')
check('both requested services persisted',[state[k]['service'] for k in ('A100','A200')],['express','express'])
check('Bob untouched by Alice batch',state['B100'],initial['B100'])
# Note boundaries and business rejection persistence.
post('valid 160 character note','A200','note',{'note':'n'*160},200)
post('locker business rejection','A200','note',{'note':'LOCKER: 1'},422)
status, row = call('read after locker rejection','GET','/api/orders/A200')
check('rejected note retains previous note',row['note'],'n'*160)
post('valid 1 character note','A200','note',{'note':'x'},200)
# Competing address writes from the same read must have one winner.
v = initial['A200']['version']
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(lambda address: call('concurrent address '+address,'POST','/api/orders/A200/address',body={'address':address,'version':v}), ['Address one','Address two']))
check('concurrent address: one success and one conflict',sorted(s for s,_ in results),[200,409])
status,row=call('read concurrent address result','GET','/api/orders/A200')
winner=[r for s,r in results if s==200]
check('address winner persists',row['address'],winner[0]['address'] if winner else 'NO WINNER')
check('address increments once',row['version'],v+1)
post('sequential stale address','A200','address',{'address':'Stale edit','version':v},409)
post('valid address length 120','A200','address',{'address':'a'*120,'version':v+1},200)
# Spend Bob's refundable fixture balance: two competing requests jointly exceed it.
remaining=initial['B100']['paid']-initial['B100']['refunded']
amount=remaining//2+1
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(lambda i: call('concurrent refund '+str(i),'POST','/api/orders/B100/refund','bob',{'amount':amount}),range(2)))
check('concurrent refunds: one success and one conflict',sorted(s for s,_ in results),[200,409])
post('refund exact remaining balance','B100','refund',{'amount':remaining-amount},200,'bob')
post('refund after exhausted balance','B100','refund',{'amount':1},409,'bob')
status,row=call('read final refund total','GET','/api/orders/B100','bob')
check('refund cumulative total capped at paid',row['refunded'],initial['B100']['paid'])
# Restore reversible edits, preserving/reporting unavoidable counter changes.
for oid in ('A100','A200'):
    service('restore service '+oid,{'ids':[oid],'service':initial[oid]['service']},200)
post('restore note','A200','note',{'note':initial['A200']['note']},200)
status,row=call('read version before address restore','GET','/api/orders/A200')
post('restore address','A200','address',{'address':initial['A200']['address'],'version':row['version']},200)
final=snapshot('final')
(OUT/'final-state.json').write_text(json.dumps(final,indent=2)+'\n')
expected=json.loads(json.dumps(initial))
expected['A200']['version']=v+3
expected['B100']['refunded']=initial['B100']['paid']
check('final state restored except disclosed refund and version',final,expected)
summary=dict(api_requests=count,checks=len(checks),passed=sum(c['passed'] for c in checks),failed=[c for c in checks if not c['passed']])
(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
