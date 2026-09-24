"""Join explicit artifact judgments to conditions; fail closed on incomplete reviews."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


def summarize(rows):
    output={}
    for arm in ['normal','template','skill']:
        selected=[r for r in rows if r['condition']==arm]
        known=[k for r in selected for k in r['review']['known']]
        extra=[a for r in selected for a in r['review']['additional']]
        eligible=[k for k in known if k['actionable']]+[a for a in extra if a['classification'] in ['valid-actionable','valid-incomplete']]
        output[arm]={'runs':len(selected),'historical_opportunities':len(known),'historical_identified':sum(k['identified'] for k in known),
                     'historical_actionable':sum(k['actionable'] for k in known),'additional':dict(Counter(a['classification'] for a in extra)),
                     'handoff':{key:sum(f['handoff'][key] for f in eligible) for key in ['reproducible','impact_clear','correction_checkable']},
                     'handoff_eligible':len(eligible),'coverage':dict(Counter(r['review']['coverage'] for r in selected)),
                     'api_requests':sum(r['api_requests'] for r in selected),
                     'median_seconds':round(statistics.median(r['elapsed_seconds'] for r in selected),2) if selected else None,
                     'runner_statuses':dict(Counter(r['status'] for r in selected)),
                     'over_api_budget':sum(r['api_requests']>180 for r in selected),
                     'missing_usage':sum(not r['usage'] for r in selected),
                     'tokens':{key:sum(u.get(key,0) for r in selected for u in r['usage']) for key in ['input_tokens','cached_input_tokens','output_tokens']},
                     'control_runs':[{'id':r['id'],'passing_evidence':r['review']['passing_evidence'],'bounded_conclusion':r['review']['bounded_conclusion'],
                                      'additional':r['review']['additional']} for r in selected if r['group']=='control'],
                     'outage_runs':[{'id':r['id'],'api_requests':r['api_requests'],'mutation_requests':r['mutation_requests'],
                                     'access':r['review']['access']} for r in selected if r['group']=='outage']}
    return output


def join(source,reviews):
    mapping=json.loads((reviews/'condition-map.json').read_text())
    schedule=json.loads((source/'schedule.json').read_text())
    assert {s['id'] for s in mapping.values()}=={s['id'] for s in schedule}
    cases={c['id']:c for c in json.loads((source/'cases.json').read_text())}
    rows=[];seen=set()
    for file in sorted(reviews.glob('batch-*/review.json')):
        for review in json.loads(file.read_text())['reviews']:
            masked=review['case_id'];assert masked in mapping and masked not in seen,masked
            seen.add(masked);spec=mapping[masked]
            expected={k['id'] for k in cases[spec['case_id']]['known']}
            assert len(review['known'])==len(expected) and {k['id'] for k in review['known']}==expected
            for known in review['known']:
                assert not known['actionable'] or known['identified']
            row=json.loads((source/spec['id']/'controller/result.json').read_text())
            assert row['condition']==spec['condition'] and row['case_id']==spec['case_id']
            row['review']=review;row['review_file']=str(file.relative_to(reviews));rows.append(row)
    assert seen==set(mapping),set(mapping)-seen
    return sorted(rows,key=lambda r:r['id'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--reviews',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();rows=join(args.source,args.reviews)
    result={'rows':rows,'summary':summarize(rows)}
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
