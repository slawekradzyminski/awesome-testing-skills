import urllib.request, urllib.error, json, hashlib
from pathlib import Path
base='http://127.0.0.1:64182'; records=[]
def req(method,path,actor=None,body=None,action=''):
    headers={'Content-Type':'application/json'}
    if actor: headers['Authorization']='Bearer demo-'+actor
    request=urllib.request.Request(base+path,headers=headers,method=method,data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(request) as r: status=r.status; raw=r.read()
    except urllib.error.HTTPError as e: status=e.code; raw=e.read()
    try: result=json.loads(raw)
    except: result=raw.decode()
    records.append(dict(method=method,path=path,actor=actor,request=body,status=status,response=result,action=action))
    return status,result
req('GET','/health',action='Build identity')
req('GET','/api/v1/cart','alice',action='Fresh read after UI Save and Cancel; expect 3 / 36')
req('GET','/api/v1/cart','bob',action='Fresh read after keyboard Cancel valid and invalid; expect 5 / 60')
req('GET','/api/v1/products','alice',action='Confirm stock remains 5')
req('GET','/api/v1/cart',action='Anonymous access rejected')
for body in [{'quantity':-1},{'quantity':1.5},{},{'quantity':None},{'quantity':'3'},{'quantity':True},{'quantity':6}]:
    req('PUT','/api/v1/cart/items/1','alice',body,'Invalid or over-stock update')
    req('GET','/api/v1/cart','alice',action='Verify rejection preserves 3 / 36')
for actor,qty in [('alice',1),('bob',2)]:
    req('PUT','/api/v1/cart/items/1',actor,{'quantity':qty},'Restore original fixture quantity')
    req('GET','/api/v1/cart',actor,action='Verify cleanup')
for path,local in [('/app.js','app/static/app.js'),('/style.css','app/static/style.css'),('/','app/static/index.html')]:
    status,body=req('GET',path,action='Compare served static asset with inspected source')
    records[-1]['response']={'matches_source':body==Path(local).read_text(),'sha256':hashlib.sha256(body.encode()).hexdigest()}
Path('evidence/http.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
print('API requests:',sum(r['path'].startswith('/api/') for r in records))
