import json, urllib.request, time
B="http://127.0.0.1:50688"; N=[0]; log=[]
def req(m,p,user=None,body=None,raw=None):
    N[0]+=1
    h={"Content-Type":"application/json"}
    if user: h["X-Test-User"]=user
    d=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r=urllib.request.Request(B+p,data=d,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=5) as x: s,b=x.status,x.read().decode()
    except urllib.error.HTTPError as e: s,b=e.code,e.read().decode()
    except Exception as e: s,b="ERR",repr(e)
    log.append({"n":N[0],"m":m,"p":p,"user":user,"body":body if raw is None else raw[:60].decode('latin1'),"status":s,"resp":b[:300]})
    print(N[0],m,p,user,body if raw is None else "<raw>", "->",s,b[:200]); return s,b
def g(i,u="alice"): return json.loads(req("GET","/api/orders/"+i,u)[1])
print("== baseline"); req("GET","/api/orders","alice"); req("GET","/api/orders",None); g("B100","alice"); g("B100","bob")
print("== F1 cumulative refund (B100 paid 4000)")
req("POST","/api/orders/B100/refund","bob",{"amount":3000})
req("POST","/api/orders/B100/refund","bob",{"amount":3000})
req("POST","/api/orders/B100/refund","bob",{"amount":4001})
g("B100","bob")
print("== refund validation"); 
for a in [0,-1,"100",1.5,True,None]: req("POST","/api/orders/A200/refund","alice",{"amount":a})
req("POST","/api/orders/B100/refund","alice",{"amount":1})
print("== F2 stale address")
o=g("A200"); v=o["version"]
req("POST","/api/orders/A200/address","alice",{"address":"Newer Street 1","version":v})
req("POST","/api/orders/A200/address","alice",{"address":"STALE Street","version":v})
req("POST","/api/orders/A200/address","alice",{"address":"Future","version":v+50})
g("A200")
print("== F3 services atomicity")
g("A100"); req("POST","/api/services","alice",{"ids":["A100","B100"],"service":"express"}); 
req("POST","/api/services","alice",{"ids":["A200","NOPE"],"service":"express"})
g("A100"); g("A200"); g("B100","bob")
print("== note")
g("A200")
req("POST","/api/orders/A200/note","alice",{"note":"  locker: 5"})
req("POST","/api/orders/A200/note","alice",{"note":"x"*161})
req("POST","/api/orders/A200/note","alice",{"note":"   "})
req("POST","/api/orders/A200/note","alice",{"note":"y"+" "*300})
g("A200")
req("POST","/api/orders/A200/note","bob",{"note":"hi"})
print("== malformed")
req("POST","/api/orders/A200/note","alice",raw=b"{bad")
req("POST","/api/orders/A200/note","alice",raw=b"[1]")
req("POST","/api/orders/A200/note","alice",raw=b"["*5000+b"]"*5000)
req("GET","/api/orders","alice")
req("POST","/api/orders/A200/note","alice",raw=b'{"note":"\xff"}')
json.dump(log,open("evidence/probe_log.json","w"),indent=1); print("requests",N[0])
