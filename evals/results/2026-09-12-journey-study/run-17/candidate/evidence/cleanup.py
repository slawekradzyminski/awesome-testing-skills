import json, urllib.request
from pathlib import Path
base='http://127.0.0.1:58576'
log=[]
def req(method,path,user,body=None):
    data=None if body is None else json.dumps(body).encode()
    with urllib.request.urlopen(urllib.request.Request(base+path,data=data,method=method,headers={'Content-Type':'application/json','X-Test-User':user})) as r:
        value=json.loads(r.read()); log.append({'method':method,'path':path,'user':user,'body':body,'status':r.status,'response':value});return value
initial=json.loads(Path('evidence/initial-state.json').read_text())
for user,orders in initial.items():
    current=req('GET','/api/orders',user)['orders']
    for old in orders:
        row=next(o for o in current if o['id']==old['id'])
        if row['note']!=old['note']:req('POST','/api/orders/'+old['id']+'/note',user,{'note':old['note']})
        if row['service']!=old['service']:req('POST','/api/services',user,{'ids':[old['id']],'service':old['service']})
        if row['address']!=old['address']:req('POST','/api/orders/'+old['id']+'/address',user,{'address':old['address'],'version':row['version']})
final={u:req('GET','/api/orders',u)['orders'] for u in initial}
diffs=[]
for user,orders in initial.items():
    for old in orders:
        new=next(o for o in final[user] if o['id']==old['id'])
        for k in old:
            if old[k]!=new[k]:diffs.append({'order':old['id'],'field':k,'initial':old[k],'final':new[k]})
Path('evidence/cleanup-results.json').write_text(json.dumps({'requests':log,'remaining_differences':diffs,'final':final},indent=2))
print(json.dumps(diffs))
