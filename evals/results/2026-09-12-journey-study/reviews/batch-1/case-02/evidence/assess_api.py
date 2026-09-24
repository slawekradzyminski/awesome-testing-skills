"""Bounded assessment of the assigned disposable runtime; reruns mutate refunds/versions."""
import json, urllib.request, urllib.error, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:58282'
records, checks = [], []

def req(label, method, path, body=None, actor='alice', raw=None):
    assert len(records) < 110, 'Reserve requests for cleanup'
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers = {'Content-Type': 'application/json'}
    if actor is not None: headers['X-Test-User'] = actor
    request = urllib.request.Request(BASE+path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    payload = response.read().decode()
    try: value = json.loads(payload)
    except ValueError: value = payload
    row = {'seq':len(records)+1, 'label':label, 'method':method, 'path':path, 'actor':actor,
           'request': raw.decode() if raw is not None else body, 'status':response.code, 'response':value}
    records.append(row)
    with (ROOT/'http.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
    return response.code, value

def check(label, actual, expected):
    checks.append({'label':label,'passed':actual == expected,'expected':expected,'actual':actual})

def post(label, suffix, body, expected=400, actor='alice'):
    status, value = req(label, 'POST', suffix, body, actor)
    check(label, status, expected)
    return value

(ROOT/'http.jsonl').write_text('')
baseline = {}
for actor, ids in [('alice',['A100','A200']),('bob',['B100'])]:
    status, result = req('baseline '+actor,'GET','/api/orders',actor=actor)
    check(actor+' lists only own orders', [o['id'] for o in result['orders']], ids)
    baseline.update({o['id']:o for o in result['orders']})
(ROOT/'baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')

# Authentication and ownership, including every mutation operation.
for actor in [None,'unknown']:
    status, _ = req('unauthorized list '+str(actor),'GET','/api/orders',actor=actor)
    check('unauthorized list '+str(actor),status,401)
    post('unauthorized mutation '+str(actor),'/api/orders/A200/note',{'note':'Forbidden'},401,actor)
for actor, target in [('alice','B100'),('bob','A200')]:
    status, _ = req('foreign read '+actor,'GET','/api/orders/'+target,actor=actor)
    check('foreign read '+actor,status,403)
    for operation, body in [('refund',{'amount':1}),('address',{'address':'Forbidden','version':1}),('note',{'note':'Forbidden'})]:
        post('foreign '+operation+' '+actor,'/api/orders/'+target+'/'+operation,body,403,actor)
    post('foreign service '+actor,'/api/services',{'ids':[target],'service':'express'},403,actor)
for actor in ['alice','bob']:
    _, result = req('verify denied mutations '+actor,'GET','/api/orders',actor=actor)
    check('denied calls preserve state '+actor,result['orders'],[o for o in baseline.values() if o['owner']==actor])

# Parsing, types, and boundaries; all must reject without changing state.
for raw in [b'{',b'[]',b'null',b'',b'{"note":"'+b'x'*8200+b'"}']:
    status, _ = req('malformed JSON/envelope '+str(len(raw)),'POST','/api/orders/A200/note',raw=raw)
    check('malformed JSON/envelope '+str(len(raw)),status,400)
for amount in [None,True,0,-1,1.5,'100']:
    post('invalid refund '+repr(amount),'/api/orders/A100/refund',{'amount':amount})
post('refund above original payment','/api/orders/A100/refund',{'amount':10001},409)
for body in [{'address':' ','version':1},{'address':'x'*121,'version':1},{'address':42,'version':1},{'address':'Valid','version':True},{'address':'Valid','version':'1'},{'address':'Valid'}]:
    post('invalid address '+str(body),'/api/orders/A200/address',body)
for body in [{'ids':[],'service':'express'},{'ids':'A200','service':'express'},{'ids':['A200',42],'service':'express'},{'ids':['A200'],'service':'overnight'},{}]:
    post('invalid services '+str(body),'/api/services',body)
for note in [None,True,' ','x'*161]:
    post('invalid note '+repr(note),'/api/orders/A200/note',{'note':note})
for note in ['LOCKER: 1','  locker: 2']:
    post('unsupported locker '+note,'/api/orders/A200/note',{'note':note},422)
_, state = req('after invalid inputs','GET','/api/orders')
check('invalid inputs preserve Alice state',state['orders'],[baseline['A100'],baseline['A200']])
for op, body in [('refund',{'amount':1}),('address',{'address':'Valid','version':1}),('note',{'note':'Valid'})]:
    post('missing order '+op,'/api/orders/MISSING/'+op,body,404)

# Refund exactly up to the payment followed by a one-cent overrun.
post('refund first partial','/api/orders/A100/refund',{'amount':6000},200)
post('refund remaining payment','/api/orders/A100/refund',{'amount':4000},200)
post('F01 cumulative refund overrun','/api/orders/A100/refund',{'amount':1},409)
_, state = req('F01 persisted refund','GET','/api/orders/A100')
check('F01 cumulative refund preserved at payment',state['refunded'],10000)

# Optimistic locking: two editors read the same version.
v = baseline['A200']['version']
post('address editor one saves','/api/orders/A200/address',{'address':'Current dispatch address','version':v},200)
post('F02 stale editor saves','/api/orders/A200/address',{'address':'Stale dispatch address','version':v},409)
_, state = req('F02 persisted stale edit','GET','/api/orders/A200')
check('F02 newer address retained',state['address'],'Current dispatch address')
check('F02 stale edit does not increment version',state['version'],v+1)
post('future address version rejected','/api/orders/A200/address',{'address':'Future address','version':state['version']+1},409)

# Batch atomicity for missing and forbidden IDs, with order reversed as controls.
for suffix, bad, expected in [('missing','MISSING',404),('forbidden','B100',403)]:
    post('F03 mixed batch '+suffix,'/api/services',{'ids':['A200',bad],'service':'express'},expected)
    _, state = req('F03 persisted service '+suffix,'GET','/api/orders/A200')
    check('F03 '+suffix+' batch atomicity',state['service'],'standard')
    post('restore service after '+suffix,'/api/services',{'ids':['A200'],'service':'standard'},200)
    post('bad ID first '+suffix,'/api/services',{'ids':[bad,'A200'],'service':'express'},expected)
    _, state = req('bad ID first state '+suffix,'GET','/api/orders/A200')
    check('bad ID first preserves service '+suffix,state['service'],'standard')
_, state = req('Bob unchanged by mixed batch','GET','/api/orders/B100',actor='bob')
check('Bob fully unchanged',state,baseline['B100'])

# Valid boundaries and persistence, then restore all reversible fixture values.
post('note max length accepted','/api/orders/A200/note',{'note':'n'*160},200)
post('locker rejection after saved note','/api/orders/A200/note',{'note':'LOCKER: 3'},422)
_, state = req('note survives rejection','GET','/api/orders/A200')
check('saved note retained after 422',state['note'],'n'*160)
post('note one char accepted','/api/orders/A200/note',{'note':'N'},200)
post('address max length accepted','/api/orders/A200/address',{'address':'a'*120,'version':state['version']},200)
post('valid multi-order service','/api/services',{'ids':['A100','A200'],'service':'express'},200)
_, state = req('successful edits persisted','GET','/api/orders')
check('both valid services persisted',[o['service'] for o in state['orders']],['express','express'])
current = {o['id']:o for o in state['orders']}
check('address boundary persisted',len(current['A200']['address']),120)
check('note boundary persisted',current['A200']['note'],'N')
for order_id in ['A100','A200']:
    post('cleanup service '+order_id,'/api/services',{'ids':[order_id],'service':baseline[order_id]['service']},200)
post('cleanup note A200','/api/orders/A200/note',{'note':baseline['A200']['note']},200)
post('cleanup address A200','/api/orders/A200/address',{'address':baseline['A200']['address'],'version':current['A200']['version']},200)
final = {}
for actor in ['alice','bob']:
    _, state = req('final fixture '+actor,'GET','/api/orders',actor=actor)
    final.update({o['id']:o for o in state['orders']})
differences = {oid:{key:{'before':baseline[oid][key],'after':value} for key,value in row.items() if value != baseline[oid][key]} for oid,row in final.items()}
differences = {oid:values for oid,values in differences.items() if values}
summary = {'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'api_requests':len(records),'checks':len(checks),'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'fixture_differences':differences}
(ROOT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(ROOT/'final-state.json').write_text(json.dumps(final,indent=2)+'\n')
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
