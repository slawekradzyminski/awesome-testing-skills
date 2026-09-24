"""Bounded assessment of the assigned disposable API; no external calls."""
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE = 'http://127.0.0.1:55995'
OUT = Path(__file__).resolve().parent
records = []
checks = []

def req(label, method, path, body=None, actor='alice', raw=None):
    assert len(records) < 120, 'API request budget exhausted'
    headers = {'Content-Type': 'application/json'}
    if actor is not None:
        headers['X-Test-User'] = actor
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status = response.status
        text = response.read().decode()
    try:
        result = json.loads(text)
    except ValueError:
        result = text
    record = {'n': len(records)+1, 'label': label, 'at': datetime.now(timezone.utc).isoformat(),
              'method': method, 'url': BASE + path, 'actor': actor,
              'request': body if raw is None else {'raw_utf8': raw.decode(errors='replace')},
              'status': status, 'response': result}
    records.append(record)
    with (OUT / 'http-transcript.jsonl').open('a') as f:
        f.write(json.dumps(record) + '\n')
    return status, result

def expect(label, actual, expected):
    checks.append({'label': label, 'expected': expected, 'actual': actual, 'pass': actual == expected})

def post(label, path, body, expected=400, actor='alice'):
    status, result = req(label, 'POST', path, body, actor)
    expect(label, status, expected)
    return status, result

def snapshot(label):
    orders = {}
    for actor in ('alice', 'bob'):
        status, result = req(label + '-' + actor, 'GET', '/api/orders', actor=actor)
        expect(label + '-' + actor, status, 200)
        orders.update({o['id']: o for o in result['orders']})
    return orders

(OUT / 'http-transcript.jsonl').write_text('')
initial = snapshot('initial')
(OUT / 'initial-state.json').write_text(json.dumps(initial, indent=2))
expect('alice-list-isolation', sorted(k for k,v in initial.items() if v['owner']=='alice'), ['A100', 'A200'])
expect('bob-list-isolation', sorted(k for k,v in initial.items() if v['owner']=='bob'), ['B100'])
# Direct read and write authorization; all attempted bodies would otherwise be valid.
for actor in (None, 'unknown'):
    for path in ('/api/orders', '/api/orders/A200'):
        status, _ = req('unauthorized-read-' + str(actor), 'GET', path, actor=actor)
        expect('unauthorized-read-' + str(actor) + path, status, 401)
    for op, body in [('refund', {'amount':1}), ('address', {'address':'Unauthorized', 'version':1}), ('note', {'note':'Unauthorized'})]:
        post('unauthorized-' + op + '-' + str(actor), '/api/orders/A200/' + op, body, 401, actor)
    post('unauthorized-service-' + str(actor), '/api/services', {'ids':['A200'], 'service':'express'}, 401, actor)
for actor, target in [('alice','B100'), ('bob','A200')]:
    status, _ = req('foreign-read-' + actor, 'GET', '/api/orders/' + target, actor=actor)
    expect('foreign-read-' + actor, status, 403)
    for op, body in [('refund', {'amount':1}), ('address', {'address':'Forbidden', 'version':1}), ('note', {'note':'Forbidden'})]:
        post('foreign-' + op + '-' + actor, '/api/orders/' + target + '/' + op, body, 403, actor)
    post('foreign-service-' + actor, '/api/services', {'ids':[target], 'service':'express'}, 403, actor)
status, _ = req('missing-read', 'GET', '/api/orders/MISSING')
expect('missing-read', status, 404)
for op, body in [('refund', {'amount':1}), ('address', {'address':'Missing', 'version':1}), ('note', {'note':'Missing'})]:
    post('missing-' + op, '/api/orders/MISSING/' + op, body, 404)
after_auth = snapshot('after-authorization')
expect('authorization-rejections-preserve-all-state', after_auth, initial)

# JSON shape and input validation, including Python bool-versus-int edge cases.
for raw in (b'{', b'[]', b'null', b'"text"', b''):
    status, _ = req('malformed-json-' + repr(raw), 'POST', '/api/orders/A200/refund', raw=raw)
    expect('malformed-json-' + repr(raw), status, 400)
for amount in (None, True, 0, -1, 1.5, '1'):
    post('invalid-refund-' + repr(amount), '/api/orders/A200/refund', {'amount':amount})
for body in ({}, {'address':' ', 'version':1}, {'address':'x'*121,'version':1}, {'address':3,'version':1}, {'address':'Valid','version':True}, {'address':'Valid','version':'1'}):
    post('invalid-address-' + repr(body), '/api/orders/A200/address', body)
for body in ({}, {'ids':[], 'service':'express'}, {'ids':'A200','service':'express'}, {'ids':[1],'service':'express'}, {'ids':['A200'],'service':'overnight'}):
    post('invalid-services-' + repr(body), '/api/services', body)
for note in (None, '', '  ', 3, 'x'*161):
    post('invalid-note-' + repr(note), '/api/orders/A200/note', {'note':note})
for note in ('LOCKER: 1', ' locker: 2'):
    post('unsupported-note-' + note, '/api/orders/A200/note', {'note':note}, 422)
after_invalid = snapshot('after-invalid-inputs')
expect('invalid-inputs-preserve-all-state', after_invalid, initial)

# An exact refund is allowed; subsequent refund must be rejected without mutation.
p = initial['A200']['paid'] - initial['A200']['refunded']
post('refund-first-part', '/api/orders/A200/refund', {'amount':p-1000}, 200)
post('refund-exact-remaining', '/api/orders/A200/refund', {'amount':1000}, 200)
post('refund-exceeds-cumulative-by-one', '/api/orders/A200/refund', {'amount':1}, 409)
post('refund-exceeds-original-payment', '/api/orders/A200/refund', {'amount':initial['A200']['paid']+1}, 409)
status, refunded = req('refund-persisted-state', 'GET', '/api/orders/A200')
expect('refund-total-cannot-exceed-paid', refunded['refunded'], refunded['paid'])

# Two clients read the same version; second client must not overwrite first.
v = initial['A200']['version']
post('address-fresh-save', '/api/orders/A200/address', {'address':'Assessment newer address', 'version':v}, 200)
post('address-stale-save', '/api/orders/A200/address', {'address':'Assessment stale overwrite', 'version':v}, 409)
status, addressed = req('address-persisted-state', 'GET', '/api/orders/A200')
expect('stale-address-preserves-newer', addressed['address'], 'Assessment newer address')
expect('stale-address-preserves-version', addressed['version'], v+1)
post('address-future-version', '/api/orders/A200/address', {'address':'Future version', 'version':addressed['version']+1}, 409)
# Valid boundary address, then restore original using latest read version.
post('address-120-characters', '/api/orders/A200/address', {'address':'x'*120, 'version':addressed['version']}, 200)
status, addressed = req('address-before-restore', 'GET', '/api/orders/A200')
post('restore-address', '/api/orders/A200/address', {'address':initial['A200']['address'], 'version':addressed['version']}, 200)

# Atomic batch failure: validate both missing and forbidden later items.
for label, target, expected in [('missing','MISSING',404), ('forbidden','B100',403)]:
    original = initial['A100']['service']
    changed = 'express' if original == 'standard' else 'standard'
    post('batch-' + label + '-later-item', '/api/services', {'ids':['A100',target], 'service':changed}, expected)
    status, state = req('batch-' + label + '-persisted-state', 'GET', '/api/orders')
    a100 = next(o for o in state['orders'] if o['id']=='A100')
    expect('batch-' + label + '-must-be-atomic', a100['service'], original)
    post('restore-service-after-' + label, '/api/services', {'ids':['A100'], 'service':original}, 200)
post('valid-batch-service', '/api/services', {'ids':['A100','A200'], 'service':'express'}, 200)
for oid in ('A100','A200'):
    post('restore-service-' + oid, '/api/services', {'ids':[oid], 'service':initial[oid]['service']}, 200)

# Valid instruction boundaries and rejection preserving a known freshly saved value.
post('note-minimum-length', '/api/orders/A200/note', {'note':'a'}, 200)
post('note-maximum-length', '/api/orders/A200/note', {'note':'n'*160}, 200)
post('note-rejected-after-save', '/api/orders/A200/note', {'note':'LOCKER: 9'}, 422)
status, noted = req('note-after-rejection', 'GET', '/api/orders/A200')
expect('rejected-note-preserves-previous', noted['note'], 'n'*160)
post('restore-note', '/api/orders/A200/note', {'note':initial['A200']['note']}, 200)
final = snapshot('final')
(OUT / 'final-state.json').write_text(json.dumps(final, indent=2))
summary = {'api_requests':len(records), 'checks':len(checks), 'passed':sum(c['pass'] for c in checks),
           'failed':[c for c in checks if not c['pass']], 'all_checks':checks,
           'remaining_state_changes':{oid:{k:{'before':initial[oid][k], 'after':value} for k,value in row.items() if value != initial[oid][k]} for oid,row in final.items() if row != initial[oid]}}
(OUT / 'results.json').write_text(json.dumps(summary, indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='all_checks'}, indent=2))
