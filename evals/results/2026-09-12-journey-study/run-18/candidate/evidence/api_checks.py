import json, urllib.request, urllib.error
BASE='http://127.0.0.1:58780'; rows=[]
def req(label,path,body=None,user='alice',expect=200,raw=None):
    headers={} if user is None else {'X-Test-User':user}
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None: headers['Content-Type']='application/json'
    r=urllib.request.Request(BASE+path,data=data,headers=headers)
    try:
        with urllib.request.urlopen(r) as f: status=f.status; value=json.load(f)
    except urllib.error.HTTPError as f: status=f.code; value=json.load(f)
    rows.append(dict(label=label,path=path,user=user,body=body,status=status,expected=expect,response=value,passed=status==expect))
    return value
initial={u:req('initial '+u,'/api/orders',user=u) for u in ('alice','bob')}
req('anonymous list','/api/orders',user=None,expect=401)
req('foreign read','/api/orders/B100',expect=403)
req('missing read','/api/orders/MISSING',expect=404)
for action,body in [('refund',{'amount':1}),('address',{'address':'Unauthorized','version':1}),('note',{'note':'Unauthorized'})]:
    req('foreign '+action,'/api/orders/B100/'+action,body,expect=403)
    req('anonymous '+action,'/api/orders/A100/'+action,body,user=None,expect=401)
for amount in [0,-1,True,1.5,'1',None]: req('invalid refund '+repr(amount),'/api/orders/A100/refund',{'amount':amount},expect=400)
req('partial refund 1','/api/orders/A100/refund',{'amount':1})
req('partial refund 2','/api/orders/A100/refund',{'amount':1})
req('cumulative over-refund','/api/orders/A100/refund',{'amount':9999},expect=409)
req('refund unchanged after rejection','/api/orders/A100')
for address,version in [(' ',1),('x'*121,1),('Valid',True),('Valid','1')]: req('invalid address','/api/orders/A200/address',{'address':address,'version':version},expect=400)
req('address save','/api/orders/A200/address',{'address':'Assessment Street','version':1})
req('stale address','/api/orders/A200/address',{'address':'Stale Street','version':1},expect=409)
req('verify newer address','/api/orders/A200')
req('restore address','/api/orders/A200/address',{'address':'20 Pine Street','version':2})
req('mixed forbidden service atomicity','/api/services',{'ids':['A100','B100'],'service':'express'},expect=403)
req('mixed missing service atomicity','/api/services',{'ids':['A100','MISSING'],'service':'express'},expect=404)
req('verify no partial service mutation','/api/orders')
for body in [{'ids':[],'service':'express'},{'ids':['A100'],'service':'premium'},{'ids':[True],'service':'express'}]: req('invalid service','/api/services',body,expect=400)
req('bulk service','/api/services',{'ids':['A100','A200'],'service':'express'})
req('restore service','/api/services',{'ids':['A100','A200'],'service':'standard'})
for note,status in [(' ',400),('x'*161,400),('LOCKER: 1',422),(' locker: 2',422)]: req('invalid note','/api/orders/A200/note',{'note':note},expect=status)
req('verify rejected notes unchanged','/api/orders/A200')
for raw in [b'[]',b'{',b'null']: req('malformed body','/api/orders/A200/note',raw=raw,expect=400)
final={u:req('final '+u,'/api/orders',user=u) for u in ('alice','bob')}
assert final['alice']['orders'][0]['refunded']==2
assert final['alice']['orders'][1]['address']=='20 Pine Street'
assert final['alice']['orders'][1]['version']==3
assert final['bob']==initial['bob']
assert all(o['service']=='standard' for o in final['alice']['orders'])
assert final['alice']['orders'][1]['note']=='Ring twice'
json.dump({'request_count':len(rows),'checks':rows,'initial':initial,'final':final},open('evidence/api-results.json','w'),indent=2)
print(len(rows),'requests;',sum(not r['passed'] for r in rows),'status failures; state assertions passed')
