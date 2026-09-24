import json, urllib.request
B="http://127.0.0.1:50690"; n=0; log=[]
def call(m,p,user="alice",body=None,raw=None):
    global n; n+=1
    h={} if user is None else {"X-Test-User":user}
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None: h["Content-Type"]="application/json"
    r=urllib.request.Request(B+p,data=data,headers=h,method=m)
    try:
        with urllib.request.urlopen(r) as x: s,t=x.status,x.read().decode()
    except urllib.error.HTTPError as e: s,t=e.code,e.read().decode()
    log.append({"n":n,"method":m,"path":p,"user":user,"body":body if raw is None else repr(raw),"status":s,"resp":t})
    print(n,m,p,user,body if raw is None else repr(raw),"->",s,t[:200])
    return s,t
# baseline
call("GET","/api/orders","alice"); call("GET","/api/orders","bob")
# auth
call("GET","/api/orders",None); call("GET","/api/orders/B100","alice")
call("POST","/api/orders/B100/refund","alice",{"amount":100})
call("POST","/api/orders/B100/note","alice",{"note":"x"})
call("POST","/api/orders/A100/note",None,{"note":"x"})
# REFUND cumulative (A200 paid 6000)
call("POST","/api/orders/A200/refund","alice",{"amount":4000})
call("POST","/api/orders/A200/refund","alice",{"amount":4000})
call("GET","/api/orders/A200","alice")
call("POST","/api/orders/A200/refund","alice",{"amount":6001})
for v in [0,-5,"100",1.5,True,None]: call("POST","/api/orders/A200/refund","alice",{"amount":v})
# ADDRESS stale version (A200 v1)
call("POST","/api/orders/A200/address","alice",{"address":"21 Pine Street","version":1})
call("POST","/api/orders/A200/address","alice",{"address":"STALE edit","version":1})
call("GET","/api/orders/A200","alice")
call("POST","/api/orders/A200/address","alice",{"address":"x","version":99})
call("POST","/api/orders/A200/address","alice",{"address":"   ","version":3})
call("POST","/api/orders/A200/address","alice",{"address":"a"*121,"version":3})
call("POST","/api/orders/A200/address","alice",{"address":"x","version":"3"})
# SERVICES atomicity
call("POST","/api/services","alice",{"ids":["A200","B100"],"service":"express"})
call("GET","/api/orders","alice"); call("GET","/api/orders/B100","bob")
call("POST","/api/services","alice",{"ids":["A100","ZZZ"],"service":"express"})
call("GET","/api/orders","alice")
call("POST","/api/services","alice",{"ids":["A100"],"service":"overnight"})
call("POST","/api/services","alice",{"ids":[],"service":"express"})
# NOTE
call("POST","/api/orders/A100/note","alice",{"note":"LOCKER: 12"})
call("POST","/api/orders/A100/note","alice",{"note":"  locker: 12"})
call("POST","/api/orders/A100/note","alice",{"note":"   "})
call("POST","/api/orders/A100/note","alice",{"note":"n"*161})
call("POST","/api/orders/A100/note","alice",{"note":"n"*160})
call("POST","/api/orders/A100/note","alice",{"note":"  "+"n"*160+"  "})
call("POST","/api/orders/A100/note","alice",{"note":123})
call("GET","/api/orders/A100","alice")
# malformed
call("POST","/api/orders/A100/note","alice",raw=b"{bad")
call("POST","/api/orders/A100/note","alice",raw=b"[1]")
call("POST","/api/orders/A100/note","alice",raw=b"\xff\xfe")
call("POST","/api/orders/A100/refund","alice",raw=b'{"amount":1e3}')
json.dump(log,open("evidence/probe_log.json","w"),indent=1)
print("requests",n)
