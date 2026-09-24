import json, time, urllib.request, urllib.error, hashlib
from pathlib import Path
BASE='http://127.0.0.1:57973'
log=Path('evidence/http.jsonl').open('w')
count=1
checks=[]
def req(label,method,path,body=None,actor='alice',raw=None):
    global count
    count+=1
    if count>115: raise RuntimeError('Request budget')
    headers={}
    if actor is not None: headers['X-Test-User']=actor
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None: headers['Content-Type']='application/json'
    start=time.monotonic()
    try:
        r=urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=headers,method=method),timeout=5)
    except urllib.error.HTTPError as e: r=e
    except Exception as e:
        log.write(json.dumps({'n':count,'label':label,'method':method,'path':path,'actor':actor,'request':body,'transport_error':str(e)})+'\n');log.flush();raise
    text=r.read().decode()
    try: value=json.loads(text)
    except ValueError: value=text
    row={'n':count,'label':label,'method':method,'path':path,'actor':actor,'request':body if raw is None else raw.decode(errors='replace'),'status':r.status,'headers':dict(r.headers),'body':value,'elapsed_ms':round((time.monotonic()-start)*1000,1)}
    log.write(json.dumps(row)+'\n');log.flush()
    print(count,label,r.status,flush=True)
    if r.status in (502,503,504): raise RuntimeError('Feature unavailable; stopping')
    return r.status,value

def check(label,actual,expected):
    checks.append({'check':label,'passed':actual==expected,'actual':actual,'expected':expected})
def get(label,oid='A200',actor='alice'):return req(label,'GET','/api/orders/'+oid,actor=actor)[1]
def post(label,op,body,oid='A200',actor='alice'):return req(label,'POST','/api/orders/'+oid+'/'+op,body,actor)
a=req('baseline-alice','GET','/api/orders')[1]['orders']
b=req('baseline-bob','GET','/api/orders',actor='bob')[1]['orders']
baseline={o['id']:o for o in a+b}
Path('evidence/baseline.json').write_text(json.dumps(baseline,indent=2))
check('Alice list ownership',[o['id'] for o in a],['A100','A200'])
check('Bob list ownership',[o['id'] for o in b],['B100'])
for actor in [None,'unknown','bob']:
    want=403 if actor=='bob' else 401
    check('read access '+str(actor),req('access-read-'+str(actor),'GET','/api/orders/A200',actor=actor)[0],want)
    for op,body in [('refund',{'amount':1}),('address',{'address':'Forbidden change','version':1}),('note',{'note':'Forbidden change'})]:
        check(op+' access '+str(actor),post('access-'+op+'-'+str(actor),op,body,actor=actor)[0],want)
    check('services access '+str(actor),req('access-services-'+str(actor),'POST','/api/services',{'ids':['A200'],'service':'express'},actor)[0],want)
check('Denied writes preserve Alice order',get('after-access-controls'),baseline['A200'])
check('Alice cannot read Bob',req('alice-read-bob','GET','/api/orders/B100')[0],403)
# Valid service change, restore, then invalid trailing IDs and inverse order.
check('Valid bulk service',req('valid-services','POST','/api/services',{'ids':['A100','A200'],'service':'express'})[0],200)
check('Valid service persists',get('valid-service-read')['service'],'express')
req('restore-valid-services','POST','/api/services',{'ids':['A100','A200'],'service':'standard'})
for suffix,want in [('MISSING',404),('B100',403)]:
    before=get('bulk-before-'+suffix)
    check('Bulk reject '+suffix,req('bulk-invalid-last-'+suffix,'POST','/api/services',{'ids':['A200',suffix],'service':'express'})[0],want)
    after=get('bulk-after-'+suffix)
    check('Bulk atomicity '+suffix,after,before)
    req('bulk-restore-'+suffix,'POST','/api/services',{'ids':['A200'],'service':before['service']})
    check('Bulk reverse rejection '+suffix,req('bulk-invalid-first-'+suffix,'POST','/api/services',{'ids':[suffix,'A200'],'service':'express'})[0],want)
    check('Bulk reverse unchanged '+suffix,get('bulk-reverse-after-'+suffix),before)
check('Bob order unchanged',get('bob-after-bulk','B100','bob'),baseline['B100'])
# Stale update against a freshly read version, including a future-version control.
old=get('address-initial')
s,new=post('address-valid-save','address',{'address':'Assessment newer address','version':old['version']})
check('Valid address accepted',s,200)
check('Version increments',new['version'],old['version']+1)
check('Valid address persists',get('address-valid-read'),new)
s,result=post('address-stale-save','address',{'address':'Assessment stale address','version':old['version']})
check('Stale version rejected',s,409)
check('Stale save preserves newer state',get('address-after-stale'),new)
current=get('address-before-future')
check('Future version rejected',post('address-future','address',{'address':'Future address','version':current['version']+1})[0],409)
check('Future rejection unchanged',get('address-after-future'),current)
post('restore-address','address',{'address':old['address'],'version':current['version']})
# Refunding up to exact paid amount then one cent beyond; changes cannot be undone.
refund_before=get('refund-before','A100')
for label,amount,want in [('partial',6000,200),('exact-balance',4000,200),('over-cumulative',1,409),('over-original',10001,409)]:
    check('Refund '+label,post('refund-'+label,'refund',{'amount':amount},'A100')[0],want)
refund_after=get('refund-after','A100')
check('Cumulative refund bounded',refund_after['refunded'],10000)
# Validation inputs chosen from parser/type/boundary branches; rejected requests must preserve state.
validation_before=get('validation-before')
for op,bodies in [('refund',[{}, {'amount':True},{'amount':1.5},{'amount':0},{'amount':-1},{'amount':'1'}]),('address',[{'address':' ','version':validation_before['version']},{'address':'x'*121,'version':validation_before['version']},{'address':'Test','version':True},{'address':'Test'}]),('note',[{}, {'note':' '},{'note':'x'*161},{'note':3}])]:
    for i,body in enumerate(bodies):check(op+' malformed '+str(i),post('validation-'+op+'-'+str(i),op,body)[0],400)
for i,body in enumerate([{'ids':[],'service':'express'},{'ids':['A200'],'service':'overnight'},{'ids':[1],'service':'express'}]):
    check('Service malformed '+str(i),req('validation-services-'+str(i),'POST','/api/services',body)[0],400)
for raw in [b'{',b'[]',b'null']:
    check('Malformed JSON '+str(raw),req('malformed-json','POST','/api/orders/A200/note',raw=raw)[0],400)
check('Malformed writes preserve state',get('validation-after'),validation_before)
check('Valid note accepted',post('note-valid','note',{'note':'Assessment ring three times'})[0],200)
saved=get('note-valid-read')
check('Valid note persists',saved['note'],'Assessment ring three times')
check('Locker rejected',post('note-locker','note',{'note':'LOCKER: 1'})[0],422)
check('Locker preserves prior note',get('note-after-rejection'),saved)
post('restore-note','note',{'note':baseline['A200']['note']})
# Restore services for all owned orders; addresses/notes already restored above.
finala=req('final-alice','GET','/api/orders')[1]['orders']
finalb=req('final-bob','GET','/api/orders',actor='bob')[1]['orders']
final={o['id']:o for o in finala+finalb}
Path('evidence/final-state.json').write_text(json.dumps(final,indent=2))
Path('evidence/checks.json').write_text(json.dumps({'api_requests_including_initial_curl':count,'checks':checks},indent=2))
Path('evidence/source-fingerprints.json').write_text(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['app/app.py','app/domain.py','app/test_domain.py','app/requirements.md']},indent=2))
print('TOTAL',count,'CHECKS',len(checks),'FAILURES',[x['check'] for x in checks if not x['passed']])
