import json, urllib.request, urllib.error
from pathlib import Path
BASE='http://127.0.0.1:58576'
log=[]
def req(method,path,body=None,user='alice',raw=None):
    headers={'Content-Type':'application/json'}
    if user: headers['X-Test-User']=user
    data=raw if raw is not None else json.dumps(body).encode() if body is not None else None
    try:
        r=urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=headers,method=method))
    except urllib.error.HTTPError as e: r=e
    value=json.loads(r.read()); log.append(dict(method=method,path=path,user=user,body=body,raw=repr(raw) if raw else None,status=r.status,response=value)); return r.status,value
def check(name,condition):
    log.append({'check':name,'passed':bool(condition)})
    if not condition: print('FAIL',name)
def get(oid,user='alice'): return req('GET','/api/orders/'+oid,user=user)[1]
initial={u:req('GET','/api/orders',user=u)[1]['orders'] for u in ['alice','bob']}
Path('evidence/initial-state.json').write_text(json.dumps(initial,indent=2))
check('Alice list isolation', [o['id'] for o in initial['alice']]==['A100','A200'])
check('Bob list isolation', [o['id'] for o in initial['bob']]==['B100'])
check('Anonymous list rejected',req('GET','/api/orders',user=None)[0]==401)
check('Anonymous mutation rejected',req('POST','/api/orders/A200/note',{'note':'unauthorized'},user=None)[0]==401)
check('Foreign order read denied',req('GET','/api/orders/B100')[0]==403)
for op,body in [('refund',{'amount':1}),('address',{'address':'bad','version':1}),('note',{'note':'bad'})]:
    check('Foreign '+op+' denied',req('POST','/api/orders/B100/'+op,body)[0]==403)
for ids in [['A200','B100'],['A200','MISSING']]:
    check('Mixed batch rejected '+str(ids),req('POST','/api/services',{'ids':ids,'service':'express'})[0] in [403,404])
    check('Mixed batch unchanged '+str(ids),get('A200')['service']=='standard')
check('Foreign order unchanged',get('B100','bob')==initial['bob'][0])
for body in [{'amount':True},{'amount':1.5},{'amount':'1'},{'amount':0},{'amount':-1},{}]:
    check('Invalid refund '+str(body),req('POST','/api/orders/B100/refund',body,'bob')[0]==400)
check('Partial refund one',req('POST','/api/orders/B100/refund',{'amount':1000},'bob')[1]['refunded']==1000)
check('Partial refund two',req('POST','/api/orders/B100/refund',{'amount':1000},'bob')[1]['refunded']==2000)
check('Cumulative excessive refund rejected',req('POST','/api/orders/B100/refund',{'amount':2001},'bob')[0]==409)
check('Excessive refund preserved total',get('B100','bob')['refunded']==2000)
b=initial['bob'][0]
check('Address save',req('POST','/api/orders/B100/address',{'address':'Temporary assessment address','version':b['version']},'bob')[1]['version']==b['version']+1)
check('Stale address rejected',req('POST','/api/orders/B100/address',{'address':'Stale assessment address','version':b['version']},'bob')[0]==409)
check('Newer address preserved',get('B100','bob')['address']=='Temporary assessment address')
for body in [{'address':' ','version':2},{'address':'x'*121,'version':2},{'address':'x','version':True}]:
    check('Invalid address '+str(body),req('POST','/api/orders/B100/address',body,'bob')[0]==400)
req('POST','/api/orders/B100/address',{'address':b['address'],'version':b['version']+1},'bob')
for note,status in [(' ',400),('x'*161,400),('LOCKER: 3',422),(' locker: 3',422)]:
    check('Note validation '+repr(note),req('POST','/api/orders/B100/note',{'note':note},'bob')[0]==status)
check('Rejected notes preserved',get('B100','bob')['note']==b['note'])
for raw in [b'{',b'[]',b'null']:
    check('Malformed body '+repr(raw),req('POST','/api/services',raw=raw)[0]==400)
check('Invalid service',req('POST','/api/services',{'ids':['A200'],'service':'unknown'})[0]==400)
check('Empty service batch',req('POST','/api/services',{'ids':[],'service':'express'})[0]==400)
check('Valid service batch',req('POST','/api/services',{'ids':['A100','A200'],'service':'express'})[0]==200)
check('Batch persisted',all(o['service']=='express' for o in req('GET','/api/orders')[1]['orders']))
req('POST','/api/services',{'ids':['A100','A200'],'service':'standard'})
Path('evidence/api-results.json').write_text(json.dumps(log,indent=2))
print(json.dumps({'requests':sum('method' in r for r in log),'checks':sum('check' in r for r in log),'failures':[r for r in log if r.get('passed') is False]}))
