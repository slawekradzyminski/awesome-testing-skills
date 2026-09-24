"""Offline consistency checks of captured results; makes no HTTP requests."""
import json
from pathlib import Path
root = Path(__file__).parent
rows = json.loads((root/'http-evidence.json').read_text())
def r(n): return rows[n-1]
def order(n, key): return next(o for o in r(n)['response']['orders'] if o['id']==key)
assert len(rows)==63
assert [r(n)['status'] for n in range(3,11)] == [401,401,403,403,403,403,403,403]
assert r(2)['response']==r(11)['response']==r(42)['response']==r(63)['response']
assert r(1)['response']==r(12)['response']
assert order(15,'A200')['refunded']==6000
assert r(16)['status']==200 and order(17,'A200')['refunded']==6001
assert r(18)['status']==409 and all(r(n)['status']==400 for n in range(19,25))
assert r(17)['response']==r(25)['response']
assert r(26)['response']['version']==2 and r(27)['status']==200
assert order(28,'A100')['address']=='Stale session overwrote newer'
assert order(28,'A100')['version']==3 and r(29)['status']==409
assert all(r(n)['status']==400 for n in range(30,33))
assert r(28)['response']==r(33)['response']
for before, mutation, after, status in [(35,36,37,404),(39,40,41,403)]:
 assert order(before,'A100')['service']=='standard'
 assert r(mutation)['status']==status and order(after,'A100')['service']=='express'
assert r(44)['status']==200 and all(o['service']=='express' for o in r(45)['response']['orders'])
assert all(r(n)['status']==400 for n in range(47,50))
assert r(50)['status']==200 and order(51,'A200')['note']=='Assessment note'
assert r(52)['status']==422 and r(51)['response']==r(53)['response']==r(60)['response']
assert all(r(n)['status']==400 for n in range(54,60))
initial=json.loads((root/'initial-state.json').read_text())
final=json.loads((root/'final-state.json').read_text())
deltas=[]
for actor in initial:
 for old,new in zip(initial[actor],final[actor]):
  for k in old:
   if old[k]!=new[k]: deltas.append((old['id'],k,old[k],new[k]))
assert deltas==[('A100','version',1,4),('A200','refunded',0,6001)],deltas
print('Captured evidence consistent: three defects confirmed; controls passed.')
print('Total API requests: 64 (one baseline curl + 63 scripted); browser actions: 0.')
print('Remaining fixture deltas:',deltas)
