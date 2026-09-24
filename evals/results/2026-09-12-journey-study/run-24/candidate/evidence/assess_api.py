import json, urllib.request, urllib.error, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
BASE='http://127.0.0.1:59820'
ROOT=Path(__file__).parent
records=[]; checks=[]; guard=threading.Lock()
def call(label, method, path, body=None, actor='alice', raw=None):
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers={'Content-Type':'application/json'}
    if actor is not None: headers['X-Test-User']=actor
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    with guard:
        seq=len(records)+1
        assert seq <= 120
        rec={'seq':seq,'label':label,'method':method,'path':path,'actor':actor,'body':body,'raw':repr(raw) if raw is not None else None}
        records.append(rec)
    try:
        with urllib.request.urlopen(req,timeout=5) as r: status, response=r.status,r.read().decode()
    except urllib.error.HTTPError as e: status,response=e.code,e.read().decode()
    except Exception as e: status,response=0,repr(e)
    try: value=json.loads(response)
    except Exception: value=response
    rec.update(status=status,response=value)
    (ROOT/'http-evidence.json').write_text(json.dumps(records,indent=2))
    return status,value

def expect(name, actual, expected):
    checks.append({'check':name,'passed':actual==expected,'expected':expected,'actual':actual})
    (ROOT/'checks.json').write_text(json.dumps(checks,indent=2))

def post(label, oid, op, body, status, actor='alice'):
    result=call(label,'POST',f'/api/orders/{oid}/{op}',body,actor)
    expect(label,result[0],status)
    return result

def state(label,actor='alice'):
    status,body=call(label,'GET','/api/orders',actor=actor)
    expect(label+' status',status,200)
    return {r['id']:r for r in body['orders']}

initial={**state('initial Alice'),**state('initial Bob','bob')}
(ROOT/'initial-state.json').write_text(json.dumps(initial,indent=2))
expect('Alice list isolated',sorted(k for k in initial if initial[k]['owner']=='alice'),['A100','A200'])
expect('Bob list isolated',list(state('Bob isolation','bob')),['B100'])
for actor in [None,'mallory']:
    expect('unauthorized list '+str(actor),call('unauthorized list','GET','/api/orders',actor=actor)[0],401)
    post('unauthorized mutation','A100','note',{'note':'unauthorized'},401,actor)
for actor,oid in [('alice','B100'),('bob','A200')]:
    expect('cross-user read '+actor,call('cross-user read','GET','/api/orders/'+oid,actor=actor)[0],403)
    for op,body in [('refund',{'amount':1}),('address',{'address':'forbidden','version':1}),('note',{'note':'forbidden'})]:
        post('cross-user '+op,oid,op,body,403,actor)
expect('authorization rejection preserves Alice',state('Alice after forbidden'),{k:v for k,v in initial.items() if v['owner']=='alice'})
expect('authorization rejection preserves Bob',state('Bob after forbidden','bob'),{'B100':initial['B100']})
for oid in ['MISSING']:
    expect('missing read',call('missing read','GET','/api/orders/'+oid)[0],404)
    for op,body in [('refund',{'amount':1}),('address',{'address':'valid','version':1}),('note',{'note':'valid'})]: post('missing '+op,oid,op,body,404)
for amount in [None,True,0,-1,1.5,'1',[],{}]: post('refund invalid '+repr(amount),'A100','refund',{'amount':amount},400)
post('refund above original','A100','refund',{'amount':10001},409)
post('first partial refund','A100','refund',{'amount':4000},200)
post('cumulative excessive refund','A100','refund',{'amount':6001},409)
expect('rejected refund preserves total',state('after excessive refund')['A100']['refunded'],4000)
post('exact remaining refund','A100','refund',{'amount':6000},200)
post('fully refunded rejects more','A100','refund',{'amount':1},409)
barrier=threading.Barrier(2)
def concurrent_refund(i):
    barrier.wait()
    return call('concurrent refund '+str(i),'POST','/api/orders/A200/refund',{'amount':4000})
with ThreadPoolExecutor(2) as pool: results=list(pool.map(concurrent_refund,[1,2]))
expect('concurrent refund status',sorted(r[0] for r in results),[200,409])
expect('concurrent refund total',state('after concurrent refunds')['A200']['refunded'],4000)
for body in [{'address':'','version':1},{'address':'   ','version':1},{'address':'x'*121,'version':1},{'address':5,'version':1},{'address':'valid','version':True},{'address':'valid','version':'1'},{'address':'valid'},{'version':1}]: post('invalid address '+repr(body),'A200','address',body,400)
post('valid maximum address','A200','address',{'address':'x'*120,'version':1},200)
post('stale address conflict','A200','address',{'address':'stale overwrite','version':1},409)
row=state('after stale address')['A200']
expect('stale edit keeps address and version',(row['address'],row['version']),('x'*120,2))
barrier=threading.Barrier(2)
def concurrent_address(i):
    barrier.wait()
    return call('concurrent address '+str(i),'POST','/api/orders/A200/address',{'address':'concurrent '+str(i),'version':2})
with ThreadPoolExecutor(2) as pool: results=list(pool.map(concurrent_address,[1,2]))
expect('concurrent address status',sorted(r[0] for r in results),[200,409])
winner=next((r[1]['address'] for r in results if r[0]==200),None)
row=state('after concurrent address')['A200']
expect('concurrent address preserves winner',(row['address'],row['version']),(winner,3))
for ids,status in [(['A100','MISSING'],404),(['A100','B100'],403),(['B100','A100'],403),(['A100','A200','MISSING'],404)]:
    expect('atomic services '+repr(ids),call('atomic services '+repr(ids),'POST','/api/services',{'ids':ids,'service':'express'})[0],status)
    expect('service rollback '+repr(ids),{k:v['service'] for k,v in state('services after rejection').items()},{'A100':'standard','A200':'standard'})
for body in [{'ids':[],'service':'express'},{'ids':'A100','service':'express'},{'ids':['A100',1],'service':'express'},{'ids':['A100'],'service':'overnight'},{'ids':['A100'],'service':[]},{'service':'express'}]:
    expect('invalid service '+repr(body),call('invalid service','POST','/api/services',body)[0],400)
expect('bulk service success',call('bulk express','POST','/api/services',{'ids':['A100','A200'],'service':'express'})[0],200)
expect('bulk service persisted',[v['service'] for v in state('bulk persisted').values()],['express','express'])
for note,status in [('',400),('   ',400),(5,400),('x'*161,400),('LOCKER: 1',422),(' locker: 2',422)]:
    post('invalid note '+repr(note),'A200','note',{'note':note},status)
expect('rejected note retains previous',state('after note rejections')['A200']['note'],initial['A200']['note'])
post('maximum valid note','A200','note',{'note':'n'*160},200)
expect('valid note persisted',state('note persisted')['A200']['note'],'n'*160)
for raw in [b'{',b'[]',b'null',b'',b'{"note":"\xff"}']:
    expect('malformed JSON '+repr(raw),call('malformed JSON','POST','/api/orders/A200/note',raw=raw)[0],400)
# Restore every reversible field; refund totals and version increments require owner reset.
current=state('before cleanup')
for oid,row in current.items():
    if row['address']!=initial[oid]['address']:
        post('restore address',oid,'address',{'address':initial[oid]['address'],'version':row['version']},200)
    if row['note']!=initial[oid]['note']:
        post('restore note',oid,'note',{'note':initial[oid]['note']},200)
expect('restore service',call('restore service','POST','/api/services',{'ids':['A100','A200'],'service':'standard'})[0],200)
final={**state('final Alice'),**state('final Bob','bob')}
(ROOT/'final-state.json').write_text(json.dumps(final,indent=2))
expect('Bob unchanged',final['B100'],initial['B100'])
for oid in ['A100','A200']:
    for field in ['address','note','service']: expect('restored '+oid+' '+field,final[oid][field],initial[oid][field])
summary={'requests':len(records),'checks':len(checks),'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']]}
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
