import json, urllib.request, urllib.error
base='http://127.0.0.1:64178'
records=[]
def request(method,path,actor=None,body=None,action=''):
    headers={'Content-Type':'application/json'}
    if actor: headers['Authorization']='Bearer demo-'+actor
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req) as response: status=response.status; result=json.load(response)
    except urllib.error.HTTPError as response: status=response.code; result=json.load(response)
    records.append(dict(method=method,path=path,actor=actor,request=body,status=status,response=result,action=action))
    return result
request('GET','/health',action='deployed build')
request('GET','/api/v1/cart','alice',action='independent persisted read after keyboard Cancel')
request('GET','/api/v1/cart','bob',action='other identity remains at fixture quantity 2')
request('GET','/api/v1/cart',action='anonymous access')
for body in [{'quantity':-1},{'quantity':1.5},{},{'quantity':None},{'quantity':'3'},{'quantity':True},{'quantity':6}]:
    request('PUT','/api/v1/cart/items/1','alice',body,'invalid quantity or stock rejection')
    request('GET','/api/v1/cart','alice',action='verify rejection preserves quantity 2')
request('PUT','/api/v1/cart/items/1','alice',{'quantity':1},'restore original fixture')
request('GET','/api/v1/cart','alice',action='verify cleanup')
request('GET','/api/v1/cart','bob',action='verify Bob unchanged')
request('GET','/api/v1/products','alice',action='verify stock remains 5')
with open('evidence/http.json','w') as out: json.dump(records,out,indent=2)
print(json.dumps({'request_count':len(records),'statuses':[r['status'] for r in records],'final_records':records[-4:]},indent=2))
