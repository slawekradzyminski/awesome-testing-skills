import urllib.request, urllib.error, json, time, pathlib, hashlib
BASE='http://127.0.0.1:49853'
root=pathlib.Path.cwd()
observations=[]
started=time.monotonic()
def req(method,path,role='alice',body=None,action=''):
    assert len(observations)<60
    headers={}
    if role: headers['Authorization']='Bearer demo-'+role
    data=None if body is None else json.dumps(body).encode()
    if data is not None: headers['Content-Type']='application/json'
    request=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    start=time.monotonic()
    try:
        response=urllib.request.urlopen(request,timeout=4)
    except urllib.error.HTTPError as error:
        response=error
    except Exception as error:
        record={'number':len(observations)+1,'method':method,'path':path,'role':role or 'anonymous','request':body,'action':action,'status':None,'error':str(error),'elapsed_ms':round((time.monotonic()-start)*1000,2)}
        observations.append(record); save(); raise SystemExit('Functional access blocked')
    raw=response.read().decode()
    try: payload=json.loads(raw)
    except ValueError: payload=raw
    record={'number':len(observations)+1,'method':method,'path':path,'role':role or 'anonymous','request':body,'authorization':'Bearer <'+role+' fixture token>' if role else None,'action':action,'status':response.status,'headers':dict(response.headers),'response':payload,'elapsed_ms':round((time.monotonic()-start)*1000,2)}
    observations.append(record); save()
    print(json.dumps(record))
    if response.status in (502,503,504): raise SystemExit('Functional access blocked: stop all probes')
    return record

def save():
    (root/'evidence/http.json').write_text(json.dumps(observations,indent=2)+'\n')

cart='/api/v1/cart'; item=cart+'/items/1'; products='/api/v1/products'
a=req('GET',cart,action='Representative feature availability and Alice baseline')
if a['status']!=200: raise SystemExit('Representative feature unavailable')
b=req('GET',cart,'bob',action='Bob baseline and identity contrast')
req('GET',products,action='Product price and stock oracle')
req('GET','/health',action='Deployed build identification')
req('GET',cart,None,action='Anonymous cart access')
req('GET',products,None,action='Anonymous product API access')
req('PUT',item,None,{'quantity':4},'Anonymous update must be rejected')
req('GET',cart,action='State after anonymous update')
req('PUT',item,'alice',{'quantity':3},'Valid update and calculated totals')
req('GET',cart,action='Confirm successful update persisted')
req('GET',cart,'bob',action='Confirm Alice update leaves Bob unchanged')
req('PUT',item,'bob',{'quantity':4},'Independent Bob update')
req('GET',cart,action='Confirm Bob update leaves Alice unchanged')
req('PUT',item,'bob',{'quantity':b['response']['items'][0]['quantity']},'Restore Bob baseline')
for label,payload in [('negative',{'quantity':-1}),('fractional',{'quantity':1.5}),('missing',{}),('null',{'quantity':None}),('string',{'quantity':'2'}),('boolean',{'quantity':True})]:
    req('PUT',item,'alice',payload,'Reject '+label+' quantity')
    req('GET',cart,action='Confirm no mutation after '+label+' quantity')
req('PUT',item,'alice',{'quantity':5},'Exact stock boundary accepted')
req('GET',cart,action='Confirm stock-boundary value and totals persisted')
req('GET',products,action='Confirm cart updates do not decrement stock')
req('PUT',item,'alice',{'quantity':6},'Overstock must return 409')
req('GET',cart,action='Confirm overstock preserves quantity five')
req('PUT',item,'alice',{'quantity':a['response']['items'][0]['quantity']},'Restore Alice baseline')
req('GET',cart,action='Verify Alice restored')
req('GET',cart,'bob',action='Verify Bob restored')
(root/'evidence/accounting.json').write_text(json.dumps({'api_requests':len(observations),'http_requests':len(observations),'browser_actions':0,'runtime_probe_seconds':round(time.monotonic()-started,2)},indent=2)+'\n')
(root/'evidence/source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('app').rglob('*') if p.is_file() and '__pycache__' not in str(p)},indent=2)+'\n')
