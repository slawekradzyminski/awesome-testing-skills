import json, urllib.request, urllib.error, pathlib, datetime, sys
ROOT=pathlib.Path(__file__).resolve().parent
BASE='http://127.0.0.1:64181'
records=[]
def call(method,path,actor='alice',body=None,action='',raw=None):
    assert len(records)<60
    headers={'Content-Type':'application/json'}
    if actor: headers['Authorization']='Bearer demo-'+actor
    data=raw.encode() if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req=urllib.request.Request(BASE+path,headers=headers,method=method,data=data)
    try:
        with urllib.request.urlopen(req,timeout=5) as r: status,payload=r.status,r.read().decode()
    except urllib.error.HTTPError as e: status,payload=e.code,e.read().decode()
    try: response=json.loads(payload)
    except ValueError: response=payload
    rec={'number':len(records)+1,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':method,'path':path,'actor':actor,'body':raw if raw is not None else body,'status':status,'response':response,'action':action}
    records.append(rec)
    (ROOT/'http.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(rec))
    return status,response
C='/api/v1/cart'; I=C+'/items/1'; P='/api/v1/products'
_,alice=call('GET',C,action='Baseline Alice cart')
_,bob=call('GET',C,'bob',action='Baseline Bob cart')
call('GET',P,action='Read price and stock')
try:
    call('GET',C,None,action='Anonymous cart rejection')
    call('GET',P,None,action='Anonymous product rejection')
    call('PUT',I,None,{'quantity':3},'Anonymous mutation rejection')
    call('GET',C,'invalid',action='Unknown token rejection')
    call('GET',C,action='Verify unauthorized attempts did not mutate Alice')
    for body in [{'quantity':-1},{'quantity':1.5},{},{'quantity':None},{'quantity':'3'},{'quantity':True},{'quantity':False},{'quantity':2.0}]:
        call('PUT',I,body=body,action='Quantity validation '+repr(body))
        call('GET',C,action='Read persisted state following validation attempt')
        if body=={'quantity':-1}:
            call('GET',C,'bob',action='Verify negative Alice mutation isolated from Bob')
            call('PUT',I,body={'quantity':1},action='Restore Alice after negative probe')
    for qty in [5,6,1000000,3]:
        call('PUT',I,body={'quantity':qty},action='Stock boundary and valid update')
        call('GET',C,action='Read persisted quantity and totals')
    call('GET',P,action='Stock remains five after accepted changes')
    call('GET',C,'bob',action='Bob still at baseline after Alice changes')
    call('PUT',I,'bob',{'quantity':4},'Bob valid update')
    call('GET',C,action='Alice unaffected by Bob update')
    call('PUT',C+'/items/999',body={'quantity':1},action='Nonexistent item update rejected')
    call('PUT',I,raw='[]',action='Non-object JSON rejected')
    call('PUT',I,raw='{bad',action='Malformed JSON rejected')
    call('GET',C,action='Cart unchanged after bad requests')
finally:
    call('PUT',I,body={'quantity':alice['items'][0]['quantity']},action='Cleanup restore Alice baseline')
    call('PUT',I,'bob',{'quantity':bob['items'][0]['quantity']},'Cleanup restore Bob baseline')
    call('GET',C,action='Verify Alice cleanup')
    call('GET',C,'bob',action='Verify Bob cleanup')
    call('GET',P,action='Verify product unchanged')
print('REQUEST_COUNT',len(records))
sys.path.insert(0,str(ROOT.parent/'app'))
from domain import Store, ApiError
s=Store(); zero=s.update('alice',1,0)
try: s.update('alice',1,1)
except ApiError as e: absent={'status':e.status,'error':e.message}
(ROOT/'local-zero.json').write_text(json.dumps({'method':'isolated in-process Store; not assigned HTTP runtime','zero_result':zero,'readd_result':absent,'bob_after':s.cart('bob')},indent=2)+'\n')
