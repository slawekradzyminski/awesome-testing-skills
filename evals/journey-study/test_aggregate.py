import unittest
from aggregate import summarize


def row(condition, control=False):
    finding = {'id': 'R1', 'identified': True, 'actionable': True,
               'impact_point': 1, 'severity_point': 1, 'acceptance_point': 1}
    return {'condition': condition, 'api_requests': 10, 'elapsed_seconds': 60,
            'app_preserved': True, 'status': 'completed', 'usage': [],
            'review': {'seeded': [] if control else [finding], 'additional': [], 'coverage_score': 2}}


class AggregationTests(unittest.TestCase):
    def test_controls_do_not_inflate_seeded_recall_or_triage_denominators(self):
        rows = [row(c, control) for c in ('normal','template','skill') for control in (False, True)]
        result = summarize(rows)
        self.assertEqual(result['normal']['runs'], 2)
        self.assertEqual(result['normal']['seeded_opportunities'], 1)
        self.assertEqual(result['normal']['triage_possible'], 3)
        self.assertEqual(result['normal']['coverage_possible'], 4)
        self.assertEqual(result['normal']['runs_missing_usage'], 2)

    def test_unsubstantiated_claims_do_not_earn_triage_points(self):
        rows = [row(c) for c in ('normal','template','skill')]
        rows[0]['review']['seeded'][0]['actionable'] = False
        rows[0]['review']['additional'] = [
            {'classification': 'unsupported', 'impact_point': 1, 'severity_point': 1, 'acceptance_point': 1},
            {'classification': 'valid', 'impact_point': 1, 'severity_point': 0, 'acceptance_point': 1}]
        result = summarize(rows)['normal']
        self.assertEqual(result['seeded_identified'], 1)
        self.assertEqual(result['seeded_actionable'], 0)
        self.assertEqual((result['triage_points'], result['triage_possible']), (2, 3))
        self.assertEqual(result['additional_claims'], {'unsupported': 1, 'valid': 1})

    def test_invalid_review_scores_fail_closed(self):
        rows = [row(c) for c in ('normal','template','skill')]
        rows[1]['review']['seeded'][0]['severity_point'] = 2
        with self.assertRaises(AssertionError):
            summarize(rows)


if __name__ == '__main__':
    unittest.main()
