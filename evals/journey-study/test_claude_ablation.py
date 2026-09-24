"""Audit-scorer checks for claude_ablation.py using synthetic traces; no model runs."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import claude_ablation as ca
import study

sys.path.insert(0, str(study.HERE / 'app'))
from domain import Desk  # noqa: E402


def row(oid, **changes):
    return {**ca.INITIAL_ORDERS[oid], **changes}


def get(oid, actor='alice', **changes):
    return {'method': 'GET', 'path': f'/api/orders/{oid}', 'actor': actor, 'request': None,
            'status': 200, 'response': row(oid, **changes)}


def get_list(*rows):
    return {'method': 'GET', 'path': '/api/orders?view=all', 'actor': 'alice', 'request': None,
            'status': 200, 'response': {'orders': list(rows)}}


def post(path, body, status, response, actor='alice'):
    return {'method': 'POST', 'path': path, 'actor': actor, 'request': body, 'status': status, 'response': response}


def refund(oid, amount, status, **after):
    return post(f'/api/orders/{oid}/refund', {'amount': amount}, status,
                row(oid, **after) if status == 200 else {'error': 'Refund exceeds remaining paid amount'})


def address(oid, value, sent_version, status, **after):
    return post(f'/api/orders/{oid}/address', {'address': value, 'version': sent_version}, status,
                row(oid, **after) if status == 200 else {'error': 'Order changed; reload before saving'})


def batch(ids, status=403):
    return post('/api/services', {'ids': ids, 'service': 'express'}, status, {'error': 'Access denied'})


OVER_REFUND = [refund('A100', 6000, 200, refunded=6000), refund('A100', 5000, 200, refunded=11000)]
STALE = [address('A100', 'Newer', 1, 200, address='Newer', version=2),
         address('A100', 'Stale', 1, 200, address='Stale', version=3)]


class ScoreAuditTests(unittest.TestCase):
    def assertSeed(self, trace, seed, triggered, observed):
        result = ca.score_audit(trace)[seed]
        self.assertEqual((result['triggered'], result['observed']), (triggered, observed), result)

    def test_all_violations_observed_by_follow_up_reads(self):
        trace = OVER_REFUND + [get('A100', refunded=11000)] + STALE + [get('A100', address='Stale', version=3)]
        trace += [batch(['A200', 'B100']), get_list(row('A100'), row('A200', service='express'))]
        result = ca.score_audit(trace)
        self.assertEqual((result['observed_count'], result['triggered_count']), (3, 3))
        self.assertEqual(result['R1']['trigger_line'], 2)
        self.assertEqual(result['R1']['observation_line'], 3)

    def test_triggering_write_without_follow_up_read_is_not_observed(self):
        self.assertSeed(OVER_REFUND, 'R1', True, False)
        self.assertSeed(STALE, 'R2', True, False)
        self.assertSeed([batch(['A200', 'B100'])], 'R3', True, False)

    def test_read_before_the_violation_does_not_count(self):
        self.assertSeed([get('A100')] + OVER_REFUND, 'R1', True, False)
        self.assertSeed([get('A100', address='Newer', version=2)] + STALE[1:], 'R2', False, False)

    def test_correct_behaviour_scores_nothing(self):
        trace = [refund('A100', 6000, 200, refunded=6000), refund('A100', 5000, 409), get('A100', refunded=6000),
                 STALE[0], address('A100', 'Stale', 1, 409), get('A100', address='Newer', version=2),
                 batch(['A200', 'B100']), get('A200')]
        self.assertEqual(ca.score_audit(trace)['observed_count'], 0)
        self.assertEqual(ca.score_audit(trace)['triggered_count'], 1)  # R3 exposing request, state preserved

    def test_read_must_show_the_violated_state(self):
        self.assertSeed(OVER_REFUND + [get('A100', refunded=6000)], 'R1', True, False)
        self.assertSeed(STALE + [get('A100', address='Newer', version=2)], 'R2', True, False)
        self.assertSeed([batch(['A200', 'B100']), get('A200')], 'R3', True, False)

    def test_legitimate_intervening_write_is_not_credited_as_partial_batch(self):
        ok = post('/api/services', {'ids': ['A200'], 'service': 'express'}, 200,
                  {'orders': [row('A200', service='express')]})
        self.assertSeed([batch(['A200', 'B100']), ok, get('A200', service='express')], 'R3', True, False)

    def test_batch_must_contain_an_inaccessible_order_after_the_changed_one(self):
        self.assertSeed([batch(['B100', 'A200']), get('A200', service='express')], 'R3', False, False)
        self.assertSeed([batch(['A200'], status=400), get('A200', service='express')], 'R3', False, False)

    def test_never_held_version_is_not_a_stale_edit(self):
        trace = [STALE[0], address('A100', 'Zero', 0, 200, address='Zero', version=3), get('A100', address='Zero')]
        self.assertSeed(trace, 'R2', False, False)

    def test_malformed_and_static_lines_are_ignored(self):
        trace = [None, {'method': 'GET', 'path': '/', 'status': 200, 'response': None}] + OVER_REFUND
        trace.append(get('A100', refunded=11000))
        self.assertEqual(ca.score_audit(trace)['R1']['observation_line'], 5)

    def test_initial_state_matches_fixture(self):
        self.assertEqual(ca.INITIAL_ORDERS, Desk().orders)


class FixtureCalibrationTest(unittest.TestCase):
    """Known-answer calibration of the scorer against the real fixture audit format (no model)."""

    def exercise(self, mutate):
        folder = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(study.HERE / 'app', folder / 'app', ignore=shutil.ignore_patterns('__pycache__'))
            if mutate:
                study.mutate(folder / 'app', 'api')
            server, base = study.start_server(folder / 'app', folder)
            try:
                for path, body in [('/api/orders/A200/refund', {'amount': 4000}), ('/api/orders/A200/refund', {'amount': 3000}),
                                   ('/api/orders/A200', None), ('/api/orders/A200/address', {'address': 'Newer', 'version': 1}),
                                   ('/api/orders/A200/address', {'address': 'Stale', 'version': 1}), ('/api/orders', None),
                                   ('/api/services', {'ids': ['A200', 'B100'], 'service': 'express'}), ('/api/orders/A200', None)]:
                    request = Request(base + path, data=json.dumps(body).encode() if body else None,
                                      headers={'X-Test-User': 'alice', 'Content-Type': 'application/json'})
                    try:
                        urlopen(request, timeout=4).close()
                    except HTTPError as error:
                        error.close()
            finally:
                server.terminate(); server.wait(timeout=5)
            return ca.score_audit(ca.load_audit(folder / 'audit.jsonl'))
        finally:
            shutil.rmtree(folder)

    def test_defective_fixture_scores_three_and_corrected_scores_none(self):
        self.assertEqual(self.exercise(True)['observed_count'], 3)
        self.assertEqual(self.exercise(False)['observed_count'], 0)


if __name__ == '__main__':
    unittest.main()
