import json, urllib.request, urllib.error
BASE='http://127.0.0.1:56486'
log=[]
def req(path, body=None, actor='alice', expected=200):
    headers={'Content-Type':'application/json'}
    if actor: headers['X-Test-User']=actor
    data=None if body is None else json.dumps(body).encode()
    r=urllib.request.Request(BASE+path,data=data,headers=headers)
    try:
        with urllib.request.urlopen(r) as response: status,value=response.status,json.load(response)
    except urllib.error.HTTPError as e: status,value=e.code,json.load(e)
    item=dict(path=path,body=body,actor=actor,status=status,response=value,expected=expected)
    log.append(item)
    assert status==expected,item
    return value
try:
    baseline={a:req('/api/orders',actor=a)['orders'] for a in ('alice','bob')}
    req('/api/orders',actor=None,expected=401)
    req('/api/orders/B100',expected=403)
    for op,body in [('note',{'note':'unauthorized'}),('address',{'address':'bad','version':1}),('refund',{'amount':1})]: req('/api/orders/B100/'+op,body,expected=403)
    req('/api/services',{'ids':['A100','B100'],'service':'express'},expected=403)
    req('/api/services',{'ids':['A100','missing'],'service':'express'},expected=404)
    assert req('/api/orders')['orders']==baseline['alice']
    assert req('/api/orders',actor='bob')['orders']==baseline['bob']
    for value in (0,-1,True,1.5,'100'):
        req('/api/orders/A200/refund',{'amount':value},expected=400)
    req('/api/orders/A200/refund',{'amount':3500})
    req('/api/orders/A200/refund',{'amount':2501},expected=409)
    assert req('/api/orders/A200')['refunded']==3500
    req('/api/orders/A200/refund',{'amount':2500})
    req('/api/orders/A200/refund',{'amount':1},expected=409)
    assert req('/api/orders/A200')['refunded']==6000
    req('/api/orders/A200/address',{'address':'Assessment address','version':1})
    req('/api/orders/A200/address',{'address':'Stale address','version':1},expected=409)
    assert req('/api/orders/A200')['address']=='Assessment address'
    for address,version in [(' ',2),('x'*121,2),('Valid',True)]: req('/api/orders/A200/address',{'address':address,'version':version},expected=400)
    req('/api/orders/A200/address',{'address':'20 Pine Street','version':2})
    for note,status in [(' ',400),('x'*161,400),('LOCKER: 1',422),(' locker: 2 ',422)]: req('/api/orders/A200/note',{'note':note},expected=status)
    assert req('/api/orders/A200')['note']=='Ring twice'
    req('/api/services',{'ids':['A100','A200'],'service':'express'})
    assert all(o['service']=='express' for o in req('/api/orders')['orders'])
    req('/api/services',{'ids':['A100','A200'],'service':'standard'})
    for body in ({'ids':[],'service':'express'},{'ids':['A100'],'service':'unknown'},[]): req('/api/services',body,expected=400)
    print('PASS',len(log),'HTTP requests; A200 refunded=6000, version=3; address/services restored.')
finally:
    with open('evidence/api-results.json','w') as f: json.dump(log,f,indent=2)
