import json, urllib.request, urllib.error
from pathlib import Path
BASE='http://127.0.0.1:56981'
log=[]
def req(method,path,body=None,user='alice',expected=200,raw=None):
    headers={} if user is None else {'X-Test-User':user}
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None: headers['Content-Type']='application/json'
    request=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request) as response: status,response_body=response.status,json.load(response)
    except urllib.error.HTTPError as error: status,response_body=error.code,json.load(error)
    log.append({'method':method,'path':path,'user':user,'request':body if raw is None else raw.decode(),'status':status,'response':response_body,'expected':expected,'pass':status==expected})
    assert status==expected, log[-1]
    return response_body
try:
    alice=req('GET','/api/orders')['orders']; bob=req('GET','/api/orders',user='bob')['orders']
    assert [o['id'] for o in alice]==['A100','A200'] and [o['id'] for o in bob]==['B100']
    req('GET','/api/orders',user=None,expected=401)
    req('GET','/api/orders/B100',expected=403)
    req('GET','/api/orders/A200',user='bob',expected=403)
    req('GET','/api/orders/missing',expected=404)
    for endpoint,body in [('refund',{'amount':1}),('address',{'address':'Forbidden','version':1}),('note',{'note':'Forbidden'})]:
        req('POST','/api/orders/B100/'+endpoint,body,expected=403)
    req('POST','/api/orders/A100/note',{'note':'Anonymous'},user=None,expected=401)
    for ids in [['A100','B100'],['A100','missing']]:
        req('POST','/api/services',{'ids':ids,'service':'express'},expected=403 if ids[-1]=='B100' else 404)
        assert req('GET','/api/orders')['orders']==alice
    req('POST','/api/services',{'ids':['A100','A200'],'service':'express'})
    assert all(o['service']=='express' for o in req('GET','/api/orders')['orders'])
    req('POST','/api/services',{'ids':['A100','A200'],'service':'standard'})
    for body in [{'ids':[],'service':'express'},{'ids':['A100'],'service':'teleport'},{'ids':[12],'service':'express'}]:
        req('POST','/api/services',body,expected=400)
    for amount in [0,-1,True,1.5,'1']:
        req('POST','/api/orders/A200/refund',{'amount':amount},expected=400)
    assert req('POST','/api/orders/A200/refund',{'amount':1000})['refunded']==1000
    assert req('POST','/api/orders/A200/refund',{'amount':5000})['refunded']==6000
    req('POST','/api/orders/A200/refund',{'amount':1},expected=409)
    assert req('GET','/api/orders/A200')['refunded']==6000
    row=req('GET','/api/orders/A200'); version=row['version']
    saved=req('POST','/api/orders/A200/address',{'address':'Assessment new address','version':version})
    assert saved['version']==version+1
    req('POST','/api/orders/A200/address',{'address':'Stale address','version':version},expected=409)
    current=req('GET','/api/orders/A200'); assert current['address']=='Assessment new address'
    for body in [{'address':' ','version':version+1},{'address':'a'*121,'version':version+1},{'address':'Valid','version':True}]:
        req('POST','/api/orders/A200/address',body,expected=400)
    req('POST','/api/orders/A200/address',{'address':row['address'],'version':version+1})
    prior=req('GET','/api/orders/A200')['note']
    for note,status in [('',400),('   ',400),('x'*161,400),('LOCKER: 1',422),(' locker: 2',422)]:
        req('POST','/api/orders/A200/note',{'note':note},expected=status)
    assert req('GET','/api/orders/A200')['note']==prior
    for raw in [b'{',b'[]',b'null']:
        req('POST','/api/orders/A200/note',raw=raw,expected=400)
    assert req('GET','/api/orders',user='bob')['orders']==bob
finally:
    for filename in ['alice-before.json','bob-before.json']:
        for original in json.loads(Path('evidence',filename).read_text())['orders']:
            if original['owner']=='alice':
                req('POST','/api/orders/'+original['id']+'/note',{'note':original['note']})
                req('POST','/api/services',{'ids':[original['id']],'service':original['service']})
    after={'alice':req('GET','/api/orders'),'bob':req('GET','/api/orders',user='bob')}
    Path('evidence/fixture-after.json').write_text(json.dumps(after,indent=2))
    Path('evidence/api-results.json').write_text(json.dumps(log,indent=2))
    print(f'{len(log)} HTTP requests recorded; all expected statuses: {all(r["pass"] for r in log)}')
    print(json.dumps(after,indent=2))
