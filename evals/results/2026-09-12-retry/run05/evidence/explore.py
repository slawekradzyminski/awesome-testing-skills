import json, time, hashlib, pathlib, urllib.request, urllib.error, subprocess
ROOT=pathlib.Path.cwd()
BASE='http://127.0.0.1:64179'
start=time.monotonic()
records=[]
def req(method,path,role='alice',body=None,raw=None,action=''):
    assert len(records)<60
    data=raw.encode() if raw is not None else json.dumps(body).encode() if body is not None else None
    headers={'Content-Type':'application/json'}
    if role: headers['Authorization']='Bearer demo-'+role if role in ('alice','bob') else 'Bearer invalid-fixture-token'
    request=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    tick=time.monotonic()
    try: response=urllib.request.urlopen(request,timeout=5)
    except urllib.error.HTTPError as e: response=e
    with response:
        text=response.read().decode()
        try: payload=json.loads(text)
        except ValueError: payload=text
        result={'number':len(records)+1,'method':method,'path':path,'role':role or 'anonymous','request':raw if raw is not None else body,'status':response.status,'headers':dict(response.headers),'body':payload,'elapsed_ms':round((time.monotonic()-tick)*1000,2),'action':action}
    records.append(result)
    (ROOT/'evidence/http.json').write_text(json.dumps(records,indent=2))
    print(result['number'],method,path,role,result['status'],payload)
    return result
cart='/api/v1/cart'; item=cart+'/items/1'; products='/api/v1/products'
req('GET','/health',None,action='Identify deployed build')
a=req('GET',cart,action='Capture Alice initial state')['body']
b=req('GET',cart,'bob',action='Capture Bob initial state')['body']
req('GET',products,action='Establish current product price and available stock')
for path in (cart,products): req('GET',path,None,action='Anonymous access boundary')
req('PUT',item,None,{'quantity':4},action='Anonymous mutation boundary')
req('GET',cart,'invalid',action='Unknown bearer token boundary')
req('GET',cart,action='Confirm rejected anonymous mutation preserved state')
req('PUT',item,body={'quantity':3},action='Representative valid update, totals and persistence')
req('GET',cart,action='Read after valid update')
req('GET',cart,'bob',action='Verify Alice update did not change Bob')
invalid=[-1,1.5,None,'3',True,False,[],{},3.0]
for val in invalid:
    req('PUT',item,body={'quantity':val},action='Reject invalid quantity type/value '+repr(val))
    req('GET',cart,action='Verify invalid update left quantity three and total 36')
req('PUT',item,body={},action='Missing quantity must reject')
req('GET',cart,action='Verify missing quantity preserved state')
req('PUT',item,body={'quantity':5},action='Stock inclusive boundary must succeed')
req('PUT',item,body={'quantity':6},action='Stock boundary plus one must reject')
req('GET',cart,action='Verify excess stock rejection left quantity five')
req('GET',products,action='Verify updates do not decrement stock')
req('PUT',item+'?username=bob',body={'quantity':4,'username':'bob'},action='Try client supplied identity override')
req('GET',cart,'bob',action='Verify spoofed identity did not change Bob')
req('GET',cart,action='Verify actor Alice received spoof attempt update')
req('PUT',item,raw='{',action='Malformed JSON parser boundary')
req('PUT',item,raw='[]',action='Non-object JSON parser boundary')
req('GET',cart,action='Verify parser failures preserved state')
req('PUT',cart+'/items/999',body={'quantity':1},action='Unknown existing-cart item')
req('GET',cart,action='Verify missing item update preserved state')
req('PUT',item,body={'quantity':a['items'][0]['quantity']},action='Restore Alice baseline')
req('GET',cart,action='Confirm Alice cleanup')
req('PUT',item,'bob',{'quantity':0},action='Terminal zero-removal boundary on disposable Bob fixture')
req('GET',cart,'bob',action='Confirm removal persisted and both totals equal zero')
req('GET',products,action='Verify removal does not change catalog stock')
metadata={'base_url':BASE,'requests':len(records),'browser_actions':0,'probe_elapsed_seconds':round(time.monotonic()-start,3),'source_revision':'No revision metadata supplied; only candidate directory inspected','source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in map(pathlib.Path,['app/app.py','app/domain.py','app/test_domain.py','requirements.md'])},'cleanup':'Alice restored to original quantity 1 and confirmed by GET. Bob item removed by terminal zero test; no supported re-add/reset endpoint. Fixture owner can restart to restore Bob. Server left running.'}
(ROOT/'evidence/session.json').write_text(json.dumps(metadata,indent=2))
