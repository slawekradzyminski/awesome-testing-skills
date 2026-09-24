import json, urllib.request, urllib.error
BASE='http://127.0.0.1:56415'
log=[]
def req(method,path,body=None,actor='alice',raw=None):
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers={'Content-Type':'application/json'}
    if actor: headers['X-Test-User']=actor
    r=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r) as response: status,value=response.status,json.load(response)
    except urllib.error.HTTPError as e: status,value=e.code,json.load(e)
    log.append(dict(method=method,path=path,actor=actor,body=body,raw=repr(raw) if raw else None,status=status,response=value))
    return status,value
def check(name,actual,expected):
    assert actual==expected,(name,actual,expected)
    print('PASS',name)
try:
    baseline={u:req('GET','/api/orders',actor=u)[1]['orders'] for u in ['alice','bob']}
    open('evidence/baseline.json','w').write(json.dumps(baseline,indent=2))
    check('Alice list ownership',[x['id'] for x in baseline['alice']],['A100','A200'])
    check('Bob list ownership',[x['id'] for x in baseline['bob']],['B100'])
    check('anonymous list',req('GET','/api/orders',actor=None)[0],401)
    check('anonymous mutation',req('POST','/api/orders/A100/note',{'note':'unauthorized'},actor=None)[0],401)
    check('foreign read',req('GET','/api/orders/B100')[0],403)
    for op,body in [('note',{'note':'unauthorized'}),('address',{'address':'unauthorized','version':1}),('refund',{'amount':1})]:
        check('foreign '+op,req('POST','/api/orders/B100/'+op,body)[0],403)
    for ids,expected in [(['A100','B100'],403),(['A100','MISSING'],404)]:
        check('batch invalid member',req('POST','/api/services',{'ids':ids,'service':'express'})[0],expected)
        check('batch atomicity',req('GET','/api/orders')[1]['orders'],baseline['alice'])
    check('batch success',req('POST','/api/services',{'ids':['A100','A200'],'service':'express'})[0],200)
    check('batch persisted',[o['service'] for o in req('GET','/api/orders')[1]['orders']],['express','express'])
    check('batch restore',req('POST','/api/services',{'ids':['A100','A200'],'service':'standard'})[0],200)
    for body in [{'ids':[],'service':'express'},{'ids':['A100'],'service':'overnight'},{'ids':[1],'service':'standard'}]:
        check('invalid services',req('POST','/api/services',body)[0],400)
    for raw in [b'{',b'[]',b'null']:
        check('malformed JSON/body',req('POST','/api/services',raw=raw)[0],400)
    for amount in [0,-1,True,1.5,'1',None]:
        check('invalid refund '+repr(amount),req('POST','/api/orders/A100/refund',{'amount':amount})[0],400)
    for amount,total in [(6000,6000),(4000,10000)]:
        s,b=req('POST','/api/orders/A100/refund',{'amount':amount}); check('partial refund',(s,b['refunded']),(200,total))
    check('cumulative refund cap',req('POST','/api/orders/A100/refund',{'amount':1})[0],409)
    check('refund unchanged after rejection',req('GET','/api/orders')[1]['orders'][0]['refunded'],10000)
    for body in [{'address':' ','version':1},{'address':'x'*121,'version':1},{'address':'valid','version':True}]:
        check('invalid address',req('POST','/api/orders/A200/address',body)[0],400)
    s,b=req('POST','/api/orders/A200/address',{'address':'Assessment address','version':1});check('address write',(s,b['version']),(200,2))
    check('stale address',req('POST','/api/orders/A200/address',{'address':'Stale overwrite','version':1})[0],409)
    check('newer address retained',req('GET','/api/orders/A200')[1]['address'],'Assessment address')
    check('address restore',req('POST','/api/orders/A200/address',{'address':'20 Pine Street','version':2})[0],200)
    for note,expected in [(' ',400),('x'*161,400),('LOCKER: 1',422),(' locker: 1 ',422),(123,400)]:
        check('invalid note '+repr(note)[:24],req('POST','/api/orders/A200/note',{'note':note})[0],expected)
    check('note preserved',req('GET','/api/orders/A200')[1]['note'],'Ring twice')
    check('160 character note',req('POST','/api/orders/A200/note',{'note':'x'*160})[0],200)
    check('note restore',req('POST','/api/orders/A200/note',{'note':'Ring twice'})[0],200)
    check('foreign order unchanged',req('GET','/api/orders',actor='bob')[1]['orders'],baseline['bob'])
finally:
    open('evidence/api-transcript.json','w').write(json.dumps(log,indent=2))
    print('API requests:',len(log))
