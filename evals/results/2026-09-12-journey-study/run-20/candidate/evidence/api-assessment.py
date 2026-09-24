import urllib.request, urllib.error, json
BASE='http://127.0.0.1:59159'
log=[]
def call(method,path,body=None,user='alice',raw=None):
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers={'Content-Type':'application/json'}
    if user: headers['X-Test-User']=user
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req) as r: status,value=r.status,json.load(r)
    except urllib.error.HTTPError as e: status,value=e.code,json.load(e)
    log.append({'method':method,'path':path,'user':user,'body':body,'raw':str(raw) if raw else None,'status':status,'response':value})
    return status,value
checks=[]
def check(name,actual,expected): checks.append({'name':name,'passed':actual==expected,'actual':actual,'expected':expected})
try:
    initial={u:call('GET','/api/orders',user=u)[1]['orders'] for u in ['alice','bob']}
    check('Alice list ownership',[x['id'] for x in initial['alice']],['A100','A200'])
    check('Bob list ownership',[x['id'] for x in initial['bob']],['B100'])
    check('anonymous read',call('GET','/api/orders',user=None)[0],401)
    check('anonymous write',call('POST','/api/orders/A200/note',{'note':'Denied'},user=None)[0],401)
    check('cross owner read',call('GET','/api/orders/B100')[0],403)
    for operation,body in [('note',{'note':'Denied'}),('refund',{'amount':1}),('address',{'address':'Denied','version':1})]:
        check('cross owner '+operation,call('POST','/api/orders/B100/'+operation,body)[0],403)
    check('Bob unchanged by forbidden writes',call('GET','/api/orders/B100',user='bob')[1],initial['bob'][0])
    for ids,expected in [(['A200','B100'],403),(['A200','MISSING'],404)]:
        before=call('GET','/api/orders/A200')[1]
        check('batch rejection '+str(ids),call('POST','/api/services',{'ids':ids,'service':'express'})[0],expected)
        check('batch atomicity '+str(ids),call('GET','/api/orders/A200')[1],before)
    for body in [{'amount':True},{'amount':0},{'amount':-1},{'amount':1.2},{'amount':'1'}]:
        check('invalid refund '+str(body),call('POST','/api/orders/B100/refund',body,user='bob')[0],400)
    check('partial refund 1',call('POST','/api/orders/B100/refund',{'amount':1000},user='bob')[1]['refunded'],1000)
    check('partial refund 2',call('POST','/api/orders/B100/refund',{'amount':2000},user='bob')[1]['refunded'],3000)
    check('cumulative excess',call('POST','/api/orders/B100/refund',{'amount':1001},user='bob')[0],409)
    check('excess leaves total',call('GET','/api/orders/B100',user='bob')[1]['refunded'],3000)
    check('exact remaining',call('POST','/api/orders/B100/refund',{'amount':1000},user='bob')[1]['refunded'],4000)
    check('fully refunded rejects',call('POST','/api/orders/B100/refund',{'amount':1},user='bob')[0],409)
    original=call('GET','/api/orders/B100',user='bob')[1]
    for body in [{'address':' ','version':1},{'address':'x'*121,'version':1},{'address':'Good','version':True}]:
        check('invalid address '+str(body),call('POST','/api/orders/B100/address',body,user='bob')[0],400)
    check('valid address',call('POST','/api/orders/B100/address',{'address':'Assessment Avenue','version':original['version']},user='bob')[0],200)
    check('stale address',call('POST','/api/orders/B100/address',{'address':'Stale Avenue','version':original['version']},user='bob')[0],409)
    newer=call('GET','/api/orders/B100',user='bob')[1]
    check('newer address preserved',newer['address'],'Assessment Avenue')
    check('version increment',newer['version'],original['version']+1)
    call('POST','/api/orders/B100/address',{'address':original['address'],'version':newer['version']},user='bob')
    for body in [{'note':''},{'note':' '},{'note':'x'*161},{'note':True}]:
        check('invalid note '+str(body),call('POST','/api/orders/B100/note',body,user='bob')[0],400)
    check('locker rejected',call('POST','/api/orders/B100/note',{'note':'LOCKER: 1'},user='bob')[0],422)
    check('rejected notes preserve saved note',call('GET','/api/orders/B100',user='bob')[1]['note'],original['note'])
    for body in [{'ids':[],'service':'express'},{'ids':['B100'],'service':'overnight'},{'ids':[1],'service':'express'}]:
        check('invalid service '+str(body),call('POST','/api/services',body,user='bob')[0],400)
    for raw in [b'{',b'[]',b'null']:
        check('malformed JSON '+str(raw),call('POST','/api/services',raw=raw)[0],400)
    final={u:call('GET','/api/orders',user=u)[1] for u in ['alice','bob']}
finally:
    with open('evidence/api-results.json','w') as f: json.dump({'checks':checks,'requests':log,'final':locals().get('final')},f,indent=2)
print(json.dumps({'checks':len(checks),'passed':sum(x['passed'] for x in checks),'requests':len(log),'failures':[x for x in checks if not x['passed']]},indent=2))
