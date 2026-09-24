"""Live assessment of the assigned disposable runtime. Re-running adds refunds/versions."""
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

BASE = 'http://127.0.0.1:58128'
OUT = Path(__file__).resolve().parent
records, checks = [], []

def call(label, method, path, body=None, actor='alice', raw=None):
    assert len(records) < 115, 'Request budget guard'
    headers = {'Content-Type': 'application/json'}
    if actor is not None:
        headers['X-Test-User'] = actor
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status, value = response.status, json.loads(response.read())
    record = {'request_number': len(records)+1, 'label': label,
              'at': datetime.now(timezone.utc).isoformat(), 'method': method,
              'path': path, 'actor': actor, 'request': body,
              'raw': raw.decode() if raw is not None else None,
              'status': status, 'response': value}
    records.append(record)
    with (OUT / 'http.jsonl').open('a') as f:
        f.write(json.dumps(record) + '\n')
    return status, value

def check(label, passed, detail=None):
    checks.append({'check': label, 'passed': bool(passed), 'detail': detail})

def post(label, path, body, expected=400, actor='alice'):
    status, value = call(label, 'POST', path, body, actor)
    check(label, status == expected, {'expected_status': expected, 'actual_status': status})
    return status, value

(OUT / 'http.jsonl').write_text('')
baseline = {}
for actor in ('alice', 'bob'):
    status, value = call('baseline ' + actor, 'GET', '/api/orders', actor=actor)
    check('list isolation ' + actor, status == 200 and all(o['owner'] == actor for o in value['orders']))
    baseline.update({o['id']: o for o in value['orders']})
(OUT / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')

try:
    for actor in (None, 'mallory'):
        status, _ = call('unauthorized list', 'GET', '/api/orders', actor=actor)
        check('unauthorized list ' + str(actor), status == 401)
        post('unauthorized mutation ' + str(actor), '/api/orders/A200/note', {'note': 'must not save'}, 401, actor)
    for actor, foreign in (('alice', 'B100'), ('bob', 'A200')):
        status, _ = call('foreign read', 'GET', '/api/orders/' + foreign, actor=actor)
        check('foreign read ' + actor, status == 403)
        for action, body in [('refund', {'amount': 1}), ('address', {'address': 'Forbidden', 'version': 1}), ('note', {'note': 'Forbidden'})]:
            post('foreign ' + action + ' ' + actor, '/api/orders/' + foreign + '/' + action, body, 403, actor)
        post('foreign service ' + actor, '/api/services', {'ids': [foreign], 'service': 'express'}, 403, actor)
    for action, body in [('refund', {'amount': 1}), ('address', {'address': 'Missing', 'version': 1}), ('note', {'note': 'Missing'})]:
        post('missing order ' + action, '/api/orders/MISSING/' + action, body, 404)

    for raw in (b'{', b'[]', b'null', b''):
        status, _ = call('malformed JSON/object', 'POST', '/api/orders/A200/refund', raw=raw)
        check('malformed body ' + repr(raw), status == 400)
    for amount in (0, -1, True, 1.5, '1', None):
        post('invalid refund ' + repr(amount), '/api/orders/A200/refund', {'amount': amount})
    for body in ({'address': '', 'version': 1}, {'address': '  ', 'version': 1}, {'address': 'x'*121, 'version': 1}, {'address': 1, 'version': 1}, {'address': 'Valid', 'version': True}, {'address': 'Valid', 'version': '1'}, {'address': 'Valid'}):
        post('invalid address', '/api/orders/A200/address', body)
    for body in ({'ids': [], 'service': 'express'}, {'ids': 'A200', 'service': 'express'}, {'ids': [1], 'service': 'express'}, {'ids': ['A200'], 'service': 'overnight'}, {'ids': ['A200']}):
        post('invalid services', '/api/services', body)
    for note in ('', '  ', 'x'*161, 1, None):
        post('invalid note', '/api/orders/A200/note', {'note': note})
    status, current = call('verify all rejected edits unchanged', 'GET', '/api/orders')
    check('rejected edits preserve Alice orders', {o['id']: o for o in current['orders']} == {k:v for k,v in baseline.items() if v['owner']=='alice'})
    status, current = call('verify Bob unchanged', 'GET', '/api/orders', actor='bob')
    check('rejected edits preserve Bob order', current['orders'] == [baseline['B100']])

    post('note maximum length accepted', '/api/orders/A200/note', {'note': 'x'*160}, 200)
    post('unsupported locker note', '/api/orders/A200/note', {'note': 'LOCKER: 1'}, 422)
    post('normalized unsupported locker note', '/api/orders/A200/note', {'note': '  locker: 1'}, 422)
    _, row = call('verify rejected locker retained note', 'GET', '/api/orders/A200')
    check('locker rejection retains saved note', row['note'] == 'x'*160)

    post('valid bulk service', '/api/services', {'ids': ['A100', 'A200'], 'service': 'express'}, 200)
    post('prepare services baseline', '/api/services', {'ids': ['A100', 'A200'], 'service': 'standard'}, 200)
    post('bulk missing second order', '/api/services', {'ids': ['A200', 'MISSING'], 'service': 'express'}, 404)
    _, row = call('read after failed missing bulk', 'GET', '/api/orders/A200')
    check('missing bulk is atomic', row['service'] == 'standard', row)
    post('restore service after missing bulk', '/api/services', {'ids': ['A200'], 'service': 'standard'}, 200)
    post('bulk forbidden second order', '/api/services', {'ids': ['A200', 'B100'], 'service': 'express'}, 403)
    _, row = call('read after failed forbidden bulk', 'GET', '/api/orders/A200')
    check('forbidden bulk is atomic', row['service'] == 'standard', row)
    _, row = call('foreign bulk target unchanged', 'GET', '/api/orders/B100', actor='bob')
    check('bulk preserves foreign order', row == baseline['B100'])

    v = baseline['A200']['version']
    post('current address version save', '/api/orders/A200/address', {'address': 'x'*120, 'version': v}, 200)
    post('stale address save', '/api/orders/A200/address', {'address': 'Stale overwrite', 'version': v}, 409)
    _, row = call('read after stale address save', 'GET', '/api/orders/A200')
    check('stale address preserves newer state', row['address'] == 'x'*120 and row['version'] == v+1, row)
    post('future address version', '/api/orders/A200/address', {'address': 'Future', 'version': row['version']+1}, 409)

    remaining = baseline['A100']['paid'] - baseline['A100']['refunded']
    post('first partial refund', '/api/orders/A100/refund', {'amount': remaining-4000}, 200)
    post('exact remaining refund', '/api/orders/A100/refund', {'amount': 4000}, 200)
    post('refund exceeds remaining by one cent', '/api/orders/A100/refund', {'amount': 1}, 409)
    _, row = call('read cumulative refund', 'GET', '/api/orders/A100')
    check('refund total never exceeds paid', row['refunded'] <= row['paid'], row)
    post('refund exceeds original payment', '/api/orders/A100/refund', {'amount': 10001}, 409)
finally:
    # Restore every reversible field using the latest version; refunds/versions need owner reset.
    final = {}
    for actor in ('alice', 'bob'):
        _, value = call('cleanup read ' + actor, 'GET', '/api/orders', actor=actor)
        for row in value['orders']:
            original = baseline[row['id']]
            if row['note'] != original['note']:
                post('restore note', '/api/orders/'+row['id']+'/note', {'note': original['note']}, 200, actor)
            if row['service'] != original['service']:
                post('restore service', '/api/services', {'ids': [row['id']], 'service': original['service']}, 200, actor)
            if row['address'] != original['address']:
                post('restore address', '/api/orders/'+row['id']+'/address', {'address': original['address'], 'version': row['version']}, 200, actor)
        _, value = call('final state ' + actor, 'GET', '/api/orders', actor=actor)
        final.update({o['id']: o for o in value['orders']})
    (OUT / 'final-state.json').write_text(json.dumps(final, indent=2)+'\n')
    (OUT / 'checks.json').write_text(json.dumps({'requests': len(records), 'checks': checks}, indent=2)+'\n')
    print(json.dumps({'requests': len(records), 'checks': len(checks), 'failed': [c for c in checks if not c['passed']]}, indent=2))
