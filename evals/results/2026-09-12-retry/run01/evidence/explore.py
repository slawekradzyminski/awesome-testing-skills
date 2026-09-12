import json,time,hashlib,pathlib,urllib.request,urllib.error
BASE='http://127.0.0.1:64091'
root=pathlib.Path(__file__).resolve().parent
records=[]
def req(method,path,role='alice',body=None,action=''):
    headers={}
    if role: headers['Authorization']='Bearer demo-'+role
    data=None if body is None else json.dumps(body).encode()
    if data is not None: headers['Content-Type']='application/json'
    start=time.monotonic()
    try:
        r=urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=headers,method=method),timeout=5)
    except urllib.error.HTTPError as e: r=e
    raw=r.read().decode()
    try: result=json.loads(raw)
    except ValueError: result=raw
    rec={'id':len(records)+1,'method':method,'path':path,'role':role or 'anonymous','request':body,'status':r.status,'headers':dict(r.headers),'response':result,'elapsed_ms':round((time.monotonic()-start)*1000,2),'action':action}
    records.append(rec)
    (root/'http.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(rec))
    return result
C='/api/v1/cart'; P='/api/v1/products'; U=C+'/items/1'
req('GET','/health',None,action='Identify runtime build')
req('GET',P,action='Establish product ID, price and stock')
req('GET',C,action='Alice baseline')
req('GET',C,'bob',action='Bob baseline')
req('GET',C,None,action='Anonymous read rejected')
req('PUT',U,None,{'quantity':4},'Anonymous write rejected')
req('GET',C,action='Confirm anonymous write did not alter Alice')
req('PUT',U,body={'quantity':3},action='Representative valid update')
req('GET',C,action='Verify successful write persisted and totals')
req('GET',C,'bob',action='Check Alice write leaves Bob untouched')
req('GET',P,action='Check cart update does not decrement stock')
req('PUT',U,body={'quantity':-1},action='Challenge missing integer lower bound')
req('GET',C,action='Check whether negative quantity persisted')
req('PUT',U,body={'quantity':1},action='Restore Alice fresh valid state')
req('PUT',U,body={'quantity':-1},action='Reproduce minimal negative update from baseline')
req('GET',C,action='Verify repeated failure persisted')
req('PUT',U,body={'quantity':1},action='Restore Alice baseline')
for body in [{'quantity':1.5},{},{'quantity':None},{'quantity':'2'},{'quantity':True},{'quantity':False}]:
    req('PUT',U,body=body,action='Quantity contract invalid value')
    req('GET',C,action='Verify rejected input leaves saved state intact')
req('PUT',U,body={'quantity':5},action='Stock boundary accepted')
req('PUT',U,body={'quantity':6},action='Stock boundary plus one rejected')
req('GET',C,action='Verify stock rejection preserves quantity five')
req('GET',P,action='Verify stock unchanged at maximum cart quantity')
req('PUT',U,body={'quantity':4,'username':'bob'},action='Check client-provided identity cannot retarget update')
req('GET',C,'bob',action='Verify Bob remains isolated after extra identity field')
req('GET',C,action='Verify authenticated Alice is actual update target')
req('PUT',U,body={'quantity':1},action='Restore Alice baseline')
req('PUT',U,'bob',{'quantity':3},'Verify Bob can update his own cart')
req('GET',C,action='Verify Bob write leaves Alice unchanged')
req('PUT',U,'bob',{'quantity':2},'Restore Bob baseline')
req('GET',C,'bob',action='Confirm Bob restored')
req('GET',C,action='Confirm Alice restored')
(root/'source-sha256.json').write_text(json.dumps({p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in ['app/app.py','app/domain.py','app/test_domain.py']},indent=2))
