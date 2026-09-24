# Reuse client helpers without replaying the mutating assessment.
exec(compile(open('evidence/probe.py').read().split("initial=snapshot('initial')")[0], 'probe-client', 'exec'))
counter=75
before=snapshot('followup baseline')
for path in ['/api/orders/A200/refund','/api/orders/A200/address','/api/orders/A200/note','/api/services']:
 post('missing required fields '+path,path,{})
post('oversized JSON body','/api/orders/A200/note',{'note':'n'*8200})
for path,body in [('/api/orders/A200/refund',{'amount':1}),('/api/orders/A200/address',{'address':'Forbidden','version':4}),('/api/orders/A200/note',{'note':'Forbidden'}),('/api/services',{'ids':['B100','A200'],'service':'express'})]:
 post('Bob forbidden write '+path,path,body,403,'bob')
check('unknown fixture rejected',call('unknown fixture','GET','/api/orders',actor='unknown')[0]==401)
check('followup rejected mutations preserve all state',snapshot('followup after denials')==before)
post('one character note','/api/orders/A200/note',{'note':'a'},200)
check('one character note persists',call('read one character note','GET','/api/orders/A200')[1]['note']=='a')
post('restore one character note','/api/orders/A200/note',{'note':before['A200']['note']},200)
# A nearby address contrast stores its normalized, bounded value.
r=post('padded 120 character address','/api/orders/A200/address',{'address':' '+'x'*120+' ','version':before['A200']['version']},200)
check('address stores bounded normalized value',len(r[1]['address'])==120)
saved=call('read normalized address','GET','/api/orders/A200')[1]
check('normalized address persisted',saved==r[1])
post('restore padded address','/api/orders/A200/address',{'address':before['A200']['address'],'version':saved['version']},200)
final=snapshot('followup final')
(OUT/'final-state.json').write_text(json.dumps(final,indent=2))
check('followup reversible fields restored',all(all(final[k][f]==before[k][f] for f in ('address','note','service')) for k in before))
(OUT/'followup-checks.json').write_text(json.dumps({'api_requests_including_baseline':counter,'checks':checks},indent=2))
print('TOTAL REQUESTS',counter)
