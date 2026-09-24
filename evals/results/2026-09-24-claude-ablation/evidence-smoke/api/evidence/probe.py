import json, urllib.request, time
B="http://127.0.0.1:51198"; log=open("evidence/http.jsonl","w"); n=[0]
def req(check, m, p, user=None, body=None):
    n[0]+=1
    h={"Content-Type":"application/json"}
    if user: h["X-Test-User"]=user
    d=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(B+p,data=d,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=5) as x: s,t=x.status,x.read().decode()
    except urllib.error.HTTPError as e: s,t=e.code,e.read().decode()
    try: t=json.loads(t)
    except Exception: pass
    e={"seq":n[0],"check":check,"t":round(time.time(),2),"role":user,"method":m,"path":p,"request":body,"status":s,"response":t}
    log.write(json.dumps(e)+"\n"); print(json.dumps(e)); return s,t
A,Bo="alice","bob"
r=req("C00","GET","/api/orders",A)
if r[0]>=500: raise SystemExit("unavailable")
req("C01","GET","/api/orders/A100")          # anonymous
req("C02","GET","/api/orders/B100",A)       # cross-user read
req("C03","POST","/api/orders/B100/note",A,{"note":"hijack"})
req("C03","GET","/api/orders/B100",Bo)
# Refund cumulative (use A200 paid 6000)
req("C04","POST","/api/orders/A200/refund",A,{"amount":4000})
req("C04","POST","/api/orders/A200/refund",A,{"amount":4000})
req("C04","GET","/api/orders/A200",A)
req("C05","POST","/api/orders/A200/refund",A,{"amount":6001})
req("C06","POST","/api/orders/A200/refund",A,{"amount":"100"})
req("C06","POST","/api/orders/A200/refund",A,{"amount":0})
req("C06","POST","/api/orders/A200/refund",A,{"amount":True})
# Address optimistic lock on A200 (version 1)
req("C07","POST","/api/orders/A200/address",A,{"address":"21 Pine Street","version":1})
req("C07","POST","/api/orders/A200/address",A,{"address":"STALE 99 Road","version":1})
req("C07","GET","/api/orders/A200",A)
req("C08","POST","/api/orders/A200/address",A,{"address":"x","version":99})
req("C09","POST","/api/orders/A200/address",A,{"address":"a"*121,"version":3})
# Services all-or-nothing
req("C10","POST","/api/services",A,{"ids":["A100","B100"],"service":"express"})
req("C10","GET","/api/orders",A)
req("C11","POST","/api/services",A,{"ids":["A200","ZZZ"],"service":"express"})
req("C11","GET","/api/orders/A200",A)
req("C12","POST","/api/services",A,{"ids":["A100","A200"],"service":"standard"})
req("C12","POST","/api/services",A,{"ids":["A100"],"service":"overnight"})
# Note
req("C13","POST","/api/orders/A100/note",A,{"note":"LOCKER: 5"})
req("C13","POST","/api/orders/A100/note",A,{"note":"  locker:5"})
req("C13","GET","/api/orders/A100",A)
req("C14","POST","/api/orders/A100/note",A,{"note":"   "})
req("C14","POST","/api/orders/A100/note",A,{"note":"a"*161})
req("C15","POST","/api/orders/A100/note",A,{"note":"Ring twice"})
req("C15","POST","/api/orders/A100/note",A,{"note":"Leave with reception"})
