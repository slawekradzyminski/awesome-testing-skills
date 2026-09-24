#!/usr/bin/env python3
"""Join reviewed outcomes to conditions; never infer semantic scores from keywords."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


POINTS = ('impact_point', 'severity_point', 'acceptance_point')


def summarize(rows):
    result = {}
    for condition in ('normal', 'template', 'skill'):
        selected = [r for r in rows if r['condition'] == condition]
        seeds = [s for r in selected for s in r['review']['seeded']]
        extra = [a for r in selected for a in r['review']['additional']]
        eligible = [s for s in seeds if s['actionable']] + [a for a in extra if a['classification'] == 'valid']
        for finding in seeds + extra:
            assert all(finding[p] in (0, 1) for p in POINTS), finding
        assert all(r['review']['coverage_score'] in (0,1,2) for r in selected)
        result[condition] = {
            'runs': len(selected),
            'seeded_opportunities': len(seeds),
            'seeded_identified': sum(s['identified'] for s in seeds),
            'seeded_actionable': sum(s['actionable'] for s in seeds),
            'additional_claims': dict(Counter(a['classification'] for a in extra)),
            'triage_points': sum(sum(f[p] for p in POINTS) for f in eligible),
            'triage_possible': 3*len(eligible),
            'coverage_points': sum(r['review']['coverage_score'] for r in selected),
            'coverage_possible': 2*len(selected),
            'api_requests_total': sum(r['api_requests'] for r in selected),
            'api_requests_median': statistics.median(r['api_requests'] for r in selected),
            'elapsed_seconds_median': round(statistics.median(r['elapsed_seconds'] for r in selected),2),
            'elapsed_seconds_total': round(sum(r['elapsed_seconds'] for r in selected),2),
            'over_360_seconds': sum(r['elapsed_seconds'] > 360 for r in selected),
            'over_120_api_requests': sum(r['api_requests'] > 120 for r in selected),
            'source_preservation_failures': sum(not r['app_preserved'] for r in selected),
            'runner_statuses': dict(Counter(r['status'] for r in selected)),
            'input_tokens': sum(u.get('input_tokens',0) for r in selected for u in r['usage']),
            'cached_input_tokens': sum(u.get('cached_input_tokens',0) for r in selected for u in r['usage']),
            'output_tokens': sum(u.get('output_tokens',0) for r in selected for u in r['usage']),
            'runs_missing_usage': sum(not r['usage'] for r in selected)}
    return result


def join(source, reviews):
    mapping = json.loads((reviews/'condition-map.json').read_text())
    rows, seen = [], set()
    for file in sorted(reviews.glob('batch-*/review.json')):
        for review in json.loads(file.read_text())['reviews']:
            case = review['case_id']
            assert case in mapping and case not in seen, case
            seen.add(case)
            spec = mapping[case]
            row = json.loads((source/spec['id']/'controller/result.json').read_text())
            expected = set(('R1','R2','R3') if spec['surface']=='api' else ('U1','U2','U3')) if spec['variant']=='defects' else set()
            assert {s['id'] for s in review['seeded']} == expected, (case, review['seeded'])
            assert len(review['seeded']) == len(expected)
            row['review'] = review
            row['review_file'] = str(file.relative_to(reviews))
            rows.append(row)
    assert seen == set(mapping), set(mapping)-seen
    return sorted(rows,key=lambda r:r['id'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--reviews',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--adjudications',type=Path)
    args=parser.parse_args()
    rows=join(args.source,args.reviews)
    raw_summary=summarize(rows)
    adjudications=json.loads(args.adjudications.read_text()) if args.adjudications else []
    for decision in adjudications:
        matching=[r for r in rows if r['id']==decision['run_id']]
        assert len(matching)==1, decision
        row=matching[0]
        findings=[a for a in row['review']['additional'] if a['title']==decision['title']]
        assert len(findings)==1 and findings[0]['classification']==decision['original_classification'], decision
        assert decision['classification'] in ('valid','unsupported','unresolved','out-of-scope')
        findings[0]['classification']=decision['classification']
        row.setdefault('adjudications',[]).append(decision)
    result={'rows':rows,'raw_review_summary':raw_summary,'adjudications':adjudications,'summary':summarize(rows)}
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],indent=2))
