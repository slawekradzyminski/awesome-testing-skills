import json, urllib.request, urllib.error
from pathlib import Path
BASE='http://127.0.0.1:56450'
log=[]
def req(method,path,body=None,user='alice',expected=200):
    headers={'Content-Type':'application/json'}
    if user: headers['X-Test-User']=user
    data=None if body is None else json.dumps(body).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=headers,method=method)) as r: status,value=r.status,json.load(r)
    except urllib.error.HTTPError as e: status,value=e.code,json.load(e)
    log.append(dict(method=method,path=path,user=user,body=body,status=status,response=value,expected=expected))
    Path('evidence/api-results.json').write_text(json.dumps(log,indent=2))
    assert status==expected,(path,status,expected)
    return value
alice=req('GET','/api/orders')['orders']; bob=req('GET','/api/orders',user='bob')['orders']
assert {o['id'] for o in alice}=={'A100','A200'} and [o['id'] for o in bob]==['B100']
req('GET','/api/orders',user=None,expected=401)
req('GET','/api/orders/B100',expected=403)
for op,body in [('note',{'note':'forbidden'}),('address',{'address':'forbidden','version':1}),('refund',{'amount':1})]:req('POST','/api/orders/B100/'+op,body,expected=403)
req('POST','/api/orders/A100/note',{'note':'anonymous'},user=None,expected=401)
for ids,status in [(['A100','B100'],403),(['A100','MISSING'],404)]:
    req('POST','/api/services',{'ids':ids,'service':'express'},expected=status)
    assert req('GET','/api/orders')['orders']==alice
assert req('GET','/api/orders',user='bob')['orders']==bob
for amount in [True,0,-1,1.5,'100']:
    req('POST','/api/orders/A200/refund',{'amount':amount},expected=400)
req('POST','/api/orders/A200/refund',{'amount':1000})
req('POST','/api/orders/A200/refund',{'amount':5001},expected=409)
assert req('GET','/api/orders/A200')['refunded']==1000
req('POST','/api/orders/A200/refund',{'amount':5000})
req('POST','/api/orders/A200/refund',{'amount':1},expected=409)
assert req('GET','/api/orders/A200')['refunded']==6000
original=next(o for o in alice if o['id']=='A200')
saved=req('POST','/api/orders/A200/address',{'address':'Assessment Street','version':original['version']})
req('POST','/api/orders/A200/address',{'address':'Stale Street','version':original['version']},expected=409)
assert req('GET','/api/orders/A200')['address']=='Assessment Street'
req('POST','/api/orders/A200/address',{'address':original['address'],'version':saved['version']})
for body in [[],{'note':''},{'note':' '*3},{'note':'x'*161}]:req('POST','/api/orders/A100/note',body,expected=400)
assert req('GET','/api/orders/A100')['note']=='Assessment: reception please'
req('POST','/api/orders/A100/note',{'note':'Leave with reception'})
print(f'{len(log)} API requests; all assertions passed. A200 refunded=6000, address restored, version=3. A100 note restored.')
