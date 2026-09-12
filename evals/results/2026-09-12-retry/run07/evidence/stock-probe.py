import json,urllib.request,urllib.error,pathlib,datetime
root=pathlib.Path(__file__).resolve().parent
records=json.loads((root/'http.json').read_text())
def call(method,path,actor,body,action):
    assert len(records)<60
    req=urllib.request.Request('http://127.0.0.1:64181'+path,method=method,headers={'Authorization':'Bearer demo-'+actor,'Content-Type':'application/json'},data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req,timeout=5) as r: status,response=r.status,json.load(r)
    except urllib.error.HTTPError as e: status,response=e.code,json.load(e)
    rec={'number':len(records)+1,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':method,'path':path,'actor':actor,'body':body,'status':status,'response':response,'action':action}
    records.append(rec);(root/'http.json').write_text(json.dumps(records,indent=2)+'\n')
    with (root/'http.txt').open('a') as out: out.write(json.dumps(rec)+'\n')
C='/api/v1/cart';I=C+'/items/1'
try:
    call('PUT',I,'alice',{'quantity':5},'Alice holds full stock quantity')
    call('PUT',I,'bob',{'quantity':5},'Bob can independently hold full stock quantity without reservation')
    call('GET','/api/v1/products','alice',None,'Catalog stock remains five with both carts at five')
    call('GET',C,'alice',None,'Alice totals at upper valid boundary')
    call('GET',C,'bob',None,'Bob totals at upper valid boundary')
finally:
    call('PUT',I,'alice',{'quantity':1},'Restore Alice original quantity')
    call('PUT',I,'bob',{'quantity':2},'Restore Bob original quantity')
    call('GET',C,'alice',None,'Final Alice cleanup verification')
    call('GET',C,'bob',None,'Final Bob cleanup verification')
print('TOTAL_API_REQUESTS',len(records))
