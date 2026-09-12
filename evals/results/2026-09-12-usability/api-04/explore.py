import json,time,urllib.request,urllib.error,pathlib
BASE='http://127.0.0.1:49528'
LOG=pathlib.Path('evidence/http.jsonl')
def req(method,path,role=None,body=None,action=''):
    count=len(LOG.read_text().splitlines()) if LOG.exists() else 0
    assert count<60
    h={'Content-Type':'application/json'}
    if role: h['Authorization']='Bearer demo-'+role
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    start=time.time()
    try:
        with urllib.request.urlopen(r,timeout=5) as resp: status=resp.status; headers=dict(resp.headers); raw=resp.read().decode()
    except urllib.error.HTTPError as e: status=e.code; headers=dict(e.headers); raw=e.read().decode()
    except Exception as e: status=None;headers={};raw=str(e)
    try: response=json.loads(raw)
    except: response=raw
    record={'id':count+1,'time':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'method':method,'path':path,'role':role or 'anonymous','request_body':body,'status':status,'headers':headers,'response':response,'elapsed_ms':round((time.time()-start)*1000),'action':action}
    with LOG.open('a') as f:f.write(json.dumps(record)+'\n')
    print(json.dumps(record))
    return record
if __name__=='__main__':
    req('GET','/api/v1/products',action='Read product identity, stock and current unit price')
    req('GET','/api/v1/cart','alice',action='Establish Alice baseline')
    req('GET','/api/v1/cart','bob',action='Establish Bob baseline')
    req('GET','/api/v1/cart',action='Anonymous cart access')
