import json, urllib.request, urllib.error
from pathlib import Path
BASE='http://127.0.0.1:57078'
log=[]
def req(name, method, path, body=None, user='alice', expected=200, raw=None):
    headers={} if user is None else {'X-Test-User':user}
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None: headers['Content-Type']='application/json'
    request=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request) as r: status,value=r.status,json.load(r)
    except urllib.error.HTTPError as e: status,value=e.code,json.load(e)
    log.append(dict(test=name,method=method,path=path,user=user,request=body if raw is None else raw.decode(),status=status,expected=expected,response=value,passed=status==expected))
    return value
try:
    req('anonymous read','GET','/api/orders',user=None,expected=401)
    req('anonymous mutation','POST','/api/orders/A100/note',{'note':'Unauthorized'},user=None,expected=401)
    a=req('alice list','GET','/api/orders'); b=req('bob list','GET','/api/orders',user='bob')
    assert {x['id'] for x in a['orders']}=={'A100','A200'} and [x['id'] for x in b['orders']]==['B100']
    req('foreign read','GET','/api/orders/B100',expected=403)
    for op,body in [('note',{'note':'Unauthorized'}),('refund',{'amount':1}),('address',{'address':'Unauthorized','version':1})]:
        req('foreign '+op,'POST','/api/orders/B100/'+op,body,expected=403)
    req('missing order','GET','/api/orders/MISSING',expected=404)
    for ids,status in [(['A100','B100'],403),(['A100','MISSING'],404)]:
        before=req('before invalid batch','GET','/api/orders')
        req('atomic invalid batch','POST','/api/services',{'ids':ids,'service':'express'},expected=status)
        after=req('after invalid batch','GET','/api/orders')
        assert before==after
    for body in [{'amount':0},{'amount':-1},{'amount':True},{'amount':1.5},{'amount':'1'},{}]:
        req('invalid refund','POST','/api/orders/A100/refund',body,expected=400)
    req('partial refund one','POST','/api/orders/A100/refund',{'amount':1000})
    req('partial refund two','POST','/api/orders/A100/refund',{'amount':2000})
    req('cumulative excessive refund','POST','/api/orders/A100/refund',{'amount':7001},expected=409)
    row=req('refund remains 3000','GET','/api/orders/A100'); assert row['refunded']==3000
    v=row['version']; original=row['address']
    req('address valid','POST','/api/orders/A100/address',{'address':'Assessment Street','version':v})
    req('address stale','POST','/api/orders/A100/address',{'address':'Stale Street','version':v},expected=409)
    row=req('newer address preserved','GET','/api/orders/A100'); assert row['address']=='Assessment Street' and row['version']==v+1
    for body in [{'address':' ','version':v+1},{'address':'x'*121,'version':v+1},{'address':'X','version':True},{'address':'X','version':'2'}]:
        req('invalid address','POST','/api/orders/A100/address',body,expected=400)
    req('restore address','POST','/api/orders/A100/address',{'address':original,'version':v+1})
    before=req('note before rejection','GET','/api/orders/A200')
    for note,status in [('LOCKER: 1',422),('  locker: 2',422),('',400),('  ',400),('x'*161,400),(True,400)]:
        req('invalid note','POST','/api/orders/A200/note',{'note':note},expected=status)
    after=req('note retained after rejections','GET','/api/orders/A200'); assert before==after
    for body in [{'ids':[],'service':'express'},{'ids':['A100'],'service':'overnight'},{'ids':[1],'service':'standard'}]:
        req('invalid service','POST','/api/services',body,expected=400)
    for raw in [b'{',b'[]',b'null']:
        req('malformed body','POST','/api/orders/A100/note',expected=400,raw=raw)
    req('valid batch express','POST','/api/services',{'ids':['A100','A200'],'service':'express'})
    row=req('batch persistence','GET','/api/orders'); assert all(x['service']=='express' for x in row['orders'])
    for filename,user in [('baseline-alice.json','alice'),('baseline-bob.json','bob')]:
        baseline=json.loads(Path('evidence',filename).read_text())
        for row in baseline['orders']:
            req('restore note','POST',f"/api/orders/{row['id']}/note",{'note':row['note']},user=user)
            req('restore service','POST','/api/services',{'ids':[row['id']],'service':row['service']},user=user)
    req('final alice state','GET','/api/orders')
    bob=req('final bob state','GET','/api/orders',user='bob'); assert bob==json.loads(Path('evidence/baseline-bob.json').read_text())
finally:
    Path('evidence/api-results.json').write_text(json.dumps(log,indent=2)+'\n')
    print(f'{len(log)} API requests; {sum(x["passed"] for x in log)} expected statuses; semantic assertions passed if exit 0.')
