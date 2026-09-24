"""Assessment of assigned disposable runtime; rerunning issues irreversible refunds."""
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

BASE = 'http://127.0.0.1:55994'
OUT = Path(__file__).resolve().parent
calls, checks = [], []

def call(method, path, body=None, actor='alice', raw=None):
    assert len(calls) < 120, 'API request budget exceeded'
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
    calls.append({'id': len(calls)+1, 'at': datetime.now(timezone.utc).isoformat(),
                  'actor': actor, 'method': method, 'path': path,
                  'body': body if raw is None else raw.decode(errors='replace'),
                  'status': status, 'response': value})
    (OUT / 'http.json').write_text(json.dumps(calls, indent=2))
    return status, value

def check(name, actual, expected):
    checks.append({'name': name, 'request_id': len(calls), 'expected': expected,
                   'actual': actual, 'pass': actual == expected})
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=2))

def post(path, body, expected, name, actor='alice', raw=None):
    status, value = call('POST', path, body, actor, raw)
    check(name, status, expected)
    return value

def snapshot():
    rows = {}
    for actor in ('alice', 'bob'):
        status, value = call('GET', '/api/orders', actor=actor)
        check(actor + ' list status', status, 200)
        rows.update({row['id']: row for row in value['orders']})
        check(actor + ' ownership filtering', all(row['owner'] == actor for row in value['orders']), True)
    return rows

baseline = snapshot()
(OUT / 'baseline.json').write_text(json.dumps(baseline, indent=2))
try:
    # Authentication and authorization: every operation, both ownership directions.
    status, _ = call('GET', '/api/orders', actor=None)
    check('anonymous list rejected', status, 401)
    status, _ = call('GET', '/api/orders/A200', actor=None)
    check('anonymous detail rejected', status, 401)
    operations = [('refund', {'amount': 1}), ('address', {'address': 'Unauthorized', 'version': 1}),
                  ('note', {'note': 'Unauthorized'})]
    for op, body in operations:
        post('/api/orders/A200/' + op, body, 401, 'anonymous ' + op, actor=None)
    post('/api/services', {'ids': ['A200'], 'service': 'express'}, 401, 'anonymous services', actor=None)
    for actor, target in [('alice', 'B100'), ('bob', 'A200')]:
        status, _ = call('GET', '/api/orders/' + target, actor=actor)
        check(actor + ' foreign detail denied', status, 403)
        for op, body in operations:
            post('/api/orders/' + target + '/' + op, body, 403, actor + ' foreign ' + op, actor)
        post('/api/services', {'ids': [target], 'service': 'express'}, 403, actor + ' foreign service', actor)
    check('denied operations preserve all records', snapshot(), baseline)

    # JSON shape and individual field type/boundary validation.
    for raw in (b'{', b'[]', b'null', b''):
        post('/api/orders/A200/refund', None, 400, 'malformed JSON object ' + repr(raw), raw=raw)
    for amount in (None, True, 0, -1, 1.5, '100'):
        post('/api/orders/A200/refund', {'amount': amount}, 400, 'invalid refund ' + repr(amount))
    post('/api/orders/A200/refund', {'amount': 6001}, 409, 'single excessive refund')
    for body in ({}, {'address': ' ', 'version': 1}, {'address': 'x'*121, 'version': 1},
                 {'address': 'Valid', 'version': True}, {'address': 'Valid', 'version': '1'}):
        post('/api/orders/A200/address', body, 400, 'invalid address ' + repr(body))
    for body in ({}, {'ids': [], 'service': 'express'}, {'ids': ['A200'], 'service': 'overnight'},
                 {'ids': ['A200', 1], 'service': 'express'}):
        post('/api/services', body, 400, 'invalid services ' + repr(body))
    for note in (None, '', ' ', 'x'*161):
        post('/api/orders/A200/note', {'note': note}, 400, 'invalid note ' + repr(note))
    check('invalid inputs preserve all records', snapshot(), baseline)

    # Refund boundary: partial + exact remainder + one cent over cumulative limit.
    refund_path = '/api/orders/A100/refund'
    post(refund_path, {'amount': 6000}, 200, 'first partial refund')
    value = post(refund_path, {'amount': 4000}, 200, 'exact remaining refund')
    check('exact full refund total', value.get('refunded'), 10000)
    post(refund_path, {'amount': 1}, 409, 'F1 cumulative excessive refund must reject')
    state = snapshot()
    check('F1 refund total must stay at payment', state['A100']['refunded'], 10000)

    # Optimistic concurrency: a newer edit must survive replay of an old version.
    address_path = '/api/orders/A200/address'
    version = state['A200']['version']
    newer = 'New address from current editor'
    value = post(address_path, {'address': newer, 'version': version}, 200, 'current version address accepted')
    check('successful address increments version', value.get('version'), version+1)
    post(address_path, {'address': 'Stale editor overwrite', 'version': version}, 409,
         'F2 stale version must reject')
    state = snapshot()
    check('F2 newer address preserved', state['A200']['address'], newer)
    check('F2 rejected stale edit does not increment version', state['A200']['version'], version+1)
    post(address_path, {'address': 'Future editor', 'version': state['A200']['version']+1}, 409,
         'future version rejected')

    # Bulk transaction failures in both orderings and both failure modes.
    for bad, expected in [('MISSING', 404), ('B100', 403)]:
        before = snapshot()
        service = 'express' if before['A200']['service'] == 'standard' else 'standard'
        post('/api/services', {'ids': ['A200', bad], 'service': service}, expected,
             'bulk ' + bad + ' returns proper error')
        after = snapshot()
        check('F3 bulk ' + bad + ' failure must preserve every order', after, before)
        post('/api/services', {'ids': ['A200'], 'service': before['A200']['service']}, 200,
             'restore service after ' + bad)
        post('/api/services', {'ids': [bad, 'A200'], 'service': service}, expected,
             'bulk ' + bad + ' first returns proper error')
        check('bulk invalid-first preserves every order ' + bad, snapshot(), before)

    # Happy path bulk update and note persistence/rejection.
    post('/api/services', {'ids': ['A100', 'A200'], 'service': 'express'}, 200, 'valid bulk express')
    state = snapshot()
    check('valid bulk persists both orders', [state[i]['service'] for i in ('A100', 'A200')], ['express', 'express'])
    for note in ('x', 'x'*160):
        post('/api/orders/A200/note', {'note': note}, 200, 'valid note length ' + str(len(note)))
        status, state = call('GET', '/api/orders/A200')
        check('valid note persisted length ' + str(len(note)), state.get('note'), note)
    saved_note = state['note']
    for note in ('LOCKER: 1', '  locker: 1'):
        post('/api/orders/A200/note', {'note': note}, 422, 'locker rejected ' + repr(note))
    status, state = call('GET', '/api/orders/A200')
    check('rejected locker preserves previous note', state.get('note'), saved_note)
finally:
    # Restore text and services. Refunds and version counters require owner reset.
    current = snapshot()
    for order_id, original in baseline.items():
        actor = original['owner']
        if current[order_id]['service'] != original['service']:
            post('/api/services', {'ids': [order_id], 'service': original['service']}, 200, 'cleanup service ' + order_id, actor)
        if current[order_id]['note'] != original['note']:
            post('/api/orders/' + order_id + '/note', {'note': original['note']}, 200, 'cleanup note ' + order_id, actor)
        if current[order_id]['address'] != original['address']:
            post('/api/orders/' + order_id + '/address', {'address': original['address'], 'version': current[order_id]['version']},
                 200, 'cleanup address ' + order_id, actor)
    final = snapshot()
    (OUT / 'final-state.json').write_text(json.dumps(final, indent=2))
    differences = {oid: {key: {'before': baseline[oid][key], 'after': row[key]}
                         for key in row if row[key] != baseline[oid][key]}
                   for oid, row in final.items() if row != baseline[oid]}
    (OUT / 'remaining-changes.json').write_text(json.dumps(differences, indent=2))
    print(json.dumps({'requests': len(calls), 'checks': len(checks),
                      'failed': [c for c in checks if not c['pass']], 'remaining_changes': differences}, indent=2))
