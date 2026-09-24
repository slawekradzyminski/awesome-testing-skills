"""Bounded one-off exploration; mutates only assigned disposable fixture runtime."""
import concurrent.futures, datetime, hashlib, json, pathlib, threading, time, urllib.request, urllib.error
BASE='http://127.0.0.1:57635'
OUT=pathlib.Path(__file__).parent
records=[]; checks=[]; mutex=threading.Lock(); count=1

def call(label, method, path, body=None, actor='alice', raw=None):
    global count
    with mutex:
        count+=1
        if count>115: raise RuntimeError('Request budget guard')
        number=count
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers={'Content-Type':'application/json'}
    if actor is not None: headers['X-Test-User']=actor
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    start=time.monotonic()
    try:
        response=urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e: response=e
    except Exception as e:
        rec={'n':number,'label':label,'method':method,'path':path,'actor':actor,'body':body,'transport_error':str(e)}
        with mutex:
            records.append(rec); (OUT/'http.json').write_text(json.dumps(records,indent=2))
        raise
    content=response.read().decode('utf-8',errors='replace')
    try: value=json.loads(content)
    except ValueError: value=content
    rec={'n':number,'label':label,'method':method,'path':path,'actor':actor,'body':body if raw is None else raw.decode('utf-8',errors='replace'),'status':response.status,'headers':dict(response.headers),'response':value,'elapsed_ms':round((time.monotonic()-start)*1000,2)}
    with mutex:
        records.append(rec); (OUT/'http.json').write_text(json.dumps(sorted(records,key=lambda r:r['n']),indent=2))
    if response.status in (502,503,504): raise RuntimeError('Feature unavailable; stop probes')
    return response.status,value

def check(label, condition):
    checks.append({'check':label,'passed':bool(condition)})
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2))
    if not condition: print('FAIL',label,flush=True)

def read(label,actor='alice'):
    status,value=call(label,'GET','/api/orders',actor=actor)
    if status!=200: raise RuntimeError('Representative feature read failed')
    return {o['id']:o for o in value['orders']}

def post(label,path,body,status=200,actor='alice'):
    s,v=call(label,'POST',path,body,actor)
    check(label+' status',s==status)
    return v

initial=read('baseline Alice'); initial.update(read('baseline Bob','bob'))
(OUT/'initial-state.json').write_text(json.dumps(initial,indent=2))
check('list ownership',set(k for k,v in initial.items() if v['owner']=='alice')=={'A100','A200'})
# Ownership contrasts and anonymous boundary, all mutation families.
for actor,oid in [('alice','B100'),('bob','A200'),(None,'A200')]:
    expected=401 if actor is None else 403
    s,_=call('read access boundary','GET','/api/orders/'+oid,actor=actor); check('read '+str(actor)+' '+oid,s==expected)
    for op,body in [('refund',{'amount':1}),('address',{'address':'Forbidden edit','version':1}),('note',{'note':'Forbidden edit'})]:
        post('write access boundary '+str(actor)+' '+op,'/api/orders/'+oid+'/'+op,body,expected,actor)
    post('service access boundary '+str(actor),'/api/services',{'ids':[oid],'service':'express'},expected,actor)
s,_=call('anonymous list','GET','/api/orders',actor=None); check('anonymous list rejected',s==401)
check('Alice unchanged after access failures',read('Alice after access failures')=={k:v for k,v in initial.items() if v['owner']=='alice'})
check('Bob unchanged after access failures',read('Bob after access failures','bob')=={'B100':initial['B100']})
# Refund strict types and cumulative limits.
for value in [0,-1,True,1.5,'1',None]:
    post('invalid refund '+repr(value),'/api/orders/A200/refund',{'amount':value},400)
post('missing refund amount','/api/orders/A200/refund',{},400)
check('invalid refunds preserve balance',read('balance after invalid refunds')['A200']['refunded']==0)
r=post('partial refund 1','/api/orders/A200/refund',{'amount':1000}); check('first partial persisted response',r.get('refunded')==1000)
r=post('partial refund 2','/api/orders/A200/refund',{'amount':2000}); check('second partial cumulative',r.get('refunded')==3000)
post('cumulative excessive refund','/api/orders/A200/refund',{'amount':3001},409)
check('excessive refund no write',read('balance after excessive refund')['A200']['refunded']==3000)
# Two competing refunds together would exceed remaining credit.
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(lambda _:call('competing refund','POST','/api/orders/A200/refund',{'amount':2000}),range(2)))
check('competing refunds exactly one accepted',sorted(s for s,v in results)==[200,409])
check('competing refund final balance',read('balance after competing refunds')['A200']['refunded']==5000)
post('exact remaining refund','/api/orders/A200/refund',{'amount':1000})
post('refund after fully refunded','/api/orders/A200/refund',{'amount':1},409)
check('refund ceiling persisted',read('fully refunded state')['A200']['refunded']==6000)
# Optimistic concurrency, validation and preservation.
for body in [{'address':'','version':1},{'address':'   ','version':1},{'address':'x'*121,'version':1},{'address':'Valid','version':True},{'address':'Valid','version':'1'},{'address':None,'version':1}]:
    post('invalid address','/api/orders/A100/address',body,400)
check('invalid address preserves all fields',read('after invalid addresses')['A100']==initial['A100'])
r=post('120 character address','/api/orders/A100/address',{'address':'X'*120,'version':1}); check('address increments version',r.get('version')==2 and r.get('address')=='X'*120)
post('stale address','/api/orders/A100/address',{'address':'Stale edit','version':1},409)
check('stale address preserves latest',read('after stale address')['A100']==r)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(lambda a:call('competing address','POST','/api/orders/A100/address',{'address':a,'version':2}),['Concurrent Alpha','Concurrent Beta']))
check('competing address exactly one accepted',sorted(s for s,v in results)==[200,409])
winner=[v for s,v in results if s==200][0]
check('competing address persisted winner',read('after competing address')['A100']==winner and winner['version']==3)
# Bulk changes are atomic regardless of invalid ID position.
post('valid express batch','/api/services',{'ids':['A100','A200'],'service':'express'})
before=read('before failed service batches')
for ids,status in [(['A100','missing'],404),(['missing','A100'],404),(['A100','B100'],403),(['B100','A100'],403)]:
    post('invalid service batch '+','.join(ids),'/api/services',{'ids':ids,'service':'standard'},status)
    check('failed batch unchanged '+','.join(ids),read('after failed batch')==before)
for body in [{'ids':[],'service':'express'},{'ids':['A100'],'service':'overnight'},{'ids':['A100',1],'service':'standard'},{'ids':'A100','service':'standard'}]:
    post('malformed services','/api/services',body,400)
check('malformed services unchanged',read('after malformed services')==before)
# Notes: accepted persistence, rejected instruction and boundary.
post('valid note','/api/orders/A200/note',{'note':'Assessment: ring three times'})
before=read('saved valid note')['A200']; check('valid note read persistence',before['note']=='Assessment: ring three times')
for note,status in [('LOCKER: 1',422),('  locker: 2',422),('',400),('  ',400),('x'*161,400),(None,400)]:
    post('rejected note '+repr(note),'/api/orders/A200/note',{'note':note},status)
    check('rejected note retains saved state',read('after rejected note')['A200']==before)
r=post('160 character note','/api/orders/A200/note',{'note':'N'*160}); check('note max accepted',r.get('note')=='N'*160)
# HTTP parser integration and nonexistent resource paths.
for raw in [b'{',b'[]',b'null',b'']:
    s,_=call('malformed JSON object','POST','/api/orders/A200/note',raw=raw); check('malformed JSON rejected',s==400)
for op,body in [('refund',{'amount':1}),('address',{'address':'Valid','version':1}),('note',{'note':'Valid'})]:
    post('missing order '+op,'/api/orders/missing/'+op,body,404)
# Restore mutable presentation fields. Refunds and version increments require owner reset.
current=read('pre-cleanup')
for oid in ['A100','A200']:
    old=initial[oid]
    if current[oid]['address']!=old['address']:
        post('restore address '+oid,'/api/orders/'+oid+'/address',{'address':old['address'],'version':current[oid]['version']})
    if current[oid]['note']!=old['note']:
        post('restore note '+oid,'/api/orders/'+oid+'/note',{'note':old['note']})
post('restore services','/api/services',{'ids':['A100','A200'],'service':'standard'})
final=read('final Alice'); final.update(read('final Bob','bob'))
(OUT/'final-state.json').write_text(json.dumps(final,indent=2))
check('reversible fields restored',all(all(final[oid][f]==initial[oid][f] for f in ['address','note','service','owner','paid']) for oid in initial))
summary={'api_requests_including_baseline_curl':count,'checks':len(checks),'failed_checks':[c for c in checks if not c['passed']],'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':{p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in ['app/app.py','app/domain.py','app/test_domain.py','app/requirements.md']},'remaining_changes':{oid:{f:{'before':initial[oid][f],'after':final[oid][f]} for f in initial[oid] if initial[oid][f]!=final[oid][f]} for oid in initial}}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
