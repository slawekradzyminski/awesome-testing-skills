import json, urllib.request, urllib.error
from pathlib import Path
BASE='http://127.0.0.1:59088'
log=[]
def req(method,path,body=None,user='alice',raw=None):
    headers={'Content-Type':'application/json'}
    if user is not None: headers['X-Test-User']=user
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r=urllib.request.Request(BASE+path,data=data,method=method,headers=headers)
    try:
        with urllib.request.urlopen(r) as f: status,result=f.status,json.load(f)
    except urllib.error.HTTPError as f: status,result=f.code,json.load(f)
    log.append(dict(method=method,path=path,user=user,request=body if raw is None else raw.decode(),status=status,response=result))
    return status,result
def expect(status,*args,**kw):
    result=req(*args,**kw); assert result[0]==status,(args,result); return result[1]
try:
    baseline={u:expect(200,'GET','/api/orders',user=u)['orders'] for u in ['alice','bob']}
    Path('evidence/api-start-state.json').write_text(json.dumps(baseline,indent=2))
    expect(401,'GET','/api/orders',user=None)
    expect(401,'POST','/api/orders/A100/note',{'note':'denied'},user=None)
    for method,path,body in [('GET','/api/orders/B100',None),('POST','/api/orders/B100/note',{'note':'denied'}),('POST','/api/orders/B100/refund',{'amount':1}),('POST','/api/orders/B100/address',{'address':'denied','version':1})]:
        expect(403,method,path,body)
    expect(403,'GET','/api/orders/A100',user='bob')
    for ids,status in [(['A100','B100'],403),(['A100','MISSING'],404)]:
        expect(status,'POST','/api/services',{'ids':ids,'service':'express'})
        rows=expect(200,'GET','/api/orders')['orders']; assert all(r['service']=='standard' for r in rows)
    expect(200,'POST','/api/services',{'ids':['A100','A200'],'service':'express'})
    expect(200,'POST','/api/services',{'ids':['A100','A200'],'service':'standard'})
    for body in [{'amount':True},{'amount':0},{'amount':-1},{'amount':1.5},{'amount':'1'}]: expect(400,'POST','/api/orders/A100/refund',body)
    for body in [{'address':' ','version':1},{'address':'a'*121,'version':1},{'address':'X','version':True}]: expect(400,'POST','/api/orders/A100/address',body)
    current=expect(200,'GET','/api/orders/A200')
    expect(200,'POST','/api/orders/A200/address',{'address':'Assessment temporary street','version':current['version']})
    expect(409,'POST','/api/orders/A200/address',{'address':'Stale edit','version':current['version']})
    newer=expect(200,'GET','/api/orders/A200'); assert newer['address']=='Assessment temporary street'
    expect(200,'POST','/api/orders/A200/address',{'address':current['address'],'version':newer['version']})
    for body in [{'note':''},{'note':' '},{'note':'x'*161},{'note':False}]: expect(400,'POST','/api/orders/A100/note',body)
    expect(422,'POST','/api/orders/A100/note',{'note':'LOCKER: 1'})
    assert expect(200,'GET','/api/orders/A100')['note']=='Leave with reception'
    for raw in [b'{',b'[]',b'null']: expect(400,'POST','/api/services',raw=raw)
    for body in [{'ids':[],'service':'express'},{'ids':['A100'],'service':'invalid'},{'ids':[1],'service':'express'}]: expect(400,'POST','/api/services',body)
    expect(200,'POST','/api/orders/A100/refund',{'amount':6000})
    expect(200,'POST','/api/orders/A100/refund',{'amount':3000})
    expect(409,'POST','/api/orders/A100/refund',{'amount':1001})
    assert expect(200,'GET','/api/orders/A100')['refunded']==9000
    expect(200,'POST','/api/orders/A100/refund',{'amount':1000})
    expect(409,'POST','/api/orders/A100/refund',{'amount':1})
    assert expect(200,'GET','/api/orders/A100')['refunded']==10000
    assert expect(200,'GET','/api/orders',user='bob')['orders']==baseline['bob']
    expect(200,'POST','/api/orders/A200/note',{'note':'Ring twice'})
    print('PASS: all API assertions; requests:',len(log))
finally:
    Path('evidence/api-check.json').write_text(json.dumps(log,indent=2))
