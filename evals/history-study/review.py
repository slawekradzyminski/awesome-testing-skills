"""Partially masked artifact review, with no testing-skill access."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import random
import shutil
import subprocess
import time
import study


def obj(properties):
    return {'type':'object','additionalProperties':False,'required':list(properties),'properties':properties}


TEXT={'type':'string'}
BOOL={'type':'boolean'}
TEXTS={'type':'array','items':TEXT}
HANDOFF=obj({'reproducible':BOOL,'impact_clear':BOOL,'correction_checkable':BOOL,'missing_information':TEXTS})
KNOWN=obj({'id':TEXT,'identified':BOOL,'actionable':BOOL,'reason':TEXT,'evidence':TEXTS,'handoff':HANDOFF})
EXTRA=obj({'title':TEXT,'classification':{'type':'string','enum':['valid-actionable','valid-incomplete','unsupported','unresolved','out-of-scope']},
           'reason':TEXT,'evidence':TEXTS,'handoff':HANDOFF})
REVIEW=obj({'case_id':TEXT,'known':{'type':'array','items':KNOWN},'additional':{'type':'array','items':EXTRA},
            'passing_evidence':BOOL,'bounded_conclusion':BOOL,
            'coverage':{'type':'string','enum':['strong','mixed','weak','not-assessable']},'coverage_reason':TEXT,
            'access':obj({'runtime_blocked_disclosed':BOOL,'source_runtime_distinguished':BOOL,
                          'useful_next_step':BOOL,'fabricated_runtime_success_or_failure':BOOL,'reason':TEXT}),
            'integrity_notes':TEXTS,'reviewed_evidence':TEXTS})
SCHEMA=obj({'reviews':{'type':'array','items':REVIEW}})


def prepare(source,out):
    out.mkdir(parents=True,exist_ok=False)
    schedule=json.loads((source/'schedule.json').read_text())
    cases={c['id']:c for c in json.loads((source/'cases.json').read_text())}
    random.Random(20260913).shuffle(schedule)
    mapping={}
    for batch_index in range((len(schedule)+3)//4):
        folder=out/f'batch-{batch_index+1}';folder.mkdir()
        entries=[]
        for index,spec in enumerate(schedule[batch_index*4:batch_index*4+4],batch_index*4+1):
            masked=f'case-{index:02}';mapping[masked]=spec
            original=source/spec['id'];dest=folder/masked
            shutil.copytree(original/'candidate',dest,ignore=shutil.ignore_patterns('skill','TASK.md','REPORT-TEMPLATE.md',
                            '__pycache__','.playwright-cli','node_modules','target','dist','.git'))
            for file in dest.rglob('*'):
                if file.is_file() and file.suffix in ('.md','.txt','.json','.jsonl','.py','.js','.ts'):
                    try:text=file.read_text()
                    except UnicodeError:continue
                    file.write_text(text.replace(str(original/'candidate'),str(dest)))
            audit=original/'controller/audit.jsonl'
            if audit.exists():shutil.copy2(audit,dest/'controller-audit.jsonl')
            result=json.loads((original/'controller/result.json').read_text())
            case=cases[spec['case_id']]
            entries.append({'case_id':masked,'surface':case['surface'],'group':case['group'],'task':case['task'],
                            'known':case['known'],'report_path':result['report_path'],'runtime_status':result['status'],
                            'elapsed_seconds':result['elapsed_seconds'],'api_requests':result['api_requests'],
                            'mutation_requests':result['mutation_requests'],'source_preserved':result['source_preserved'],
                            'fixture_limits':'Native app; in-memory test data; controlled gateway latency; optional external services excluded. Legacy cart uses fixed localhost ports. No source mutations. UI setup uses a compatible backend from another pinned revision.'})
        study.write_json(folder/'cases.json',entries)
        study.write_json(folder/'schema.json',SCHEMA)
        protocol=(source/'protocol.md').read_text()
        (folder/'RUBRIC.md').write_text(protocol[protocol.index('## Outcomes fixed before runs'):])
        (folder/'TASK.md').write_text('''Review the reports in cases.json against RUBRIC.md. Work only inside this batch.
Do not inspect parents, other batches, skill files, condition mappings, Git history or external sources.
Do not run the application or reproduction scripts. Read each report, its decisive evidence,
relevant original source and supplied controller audit. Open screenshots supporting visual claims.
Judge actual testing and reproducibility, not formatting, report length or compliance with a template.

Condition labels are withheld but text may reveal guidance. Do not infer or score the condition.
Score every known fault including missed ones. Source suspicion can identify a fault but cannot
make it runtime-actionable. Audits corroborate candidate evidence, not replace missing reproduction.
For each additional confirmed claim classify valid-actionable, valid-incomplete, unsupported,
unresolved intent, or out-of-scope. Suggestions and honestly qualified risks are not false positives.
Corrected controls can contain other valid defects. Distinguish product behavior from fixture limits,
historical frontend/newer-backend compatibility, intentionally blocked external features and injections.
User tasks exclude documentation-only defects. UI investigation excludes catalog/account administration;
API investigation covers account registration/signin/own data and excludes catalog/orders/email delivery.

Handoff booleans describe whether an actual recipient has the information to reproduce, understand
demonstrated impact, and verify correction. Do not award them just because a heading exists.
For missed or unsubstantiated findings use false handoff booleans. Explain missing information.
Coverage strength requires cited examples of meaningful risk selection and any consequential omitted
scope, not a count of checks or screenshots. Passing evidence requires executed observations.
For outage cases, functional application testing is blocked despite any passing source/unit checks.
Report access distinctions and next steps, and identify fabricated runtime conclusions explicitly.
Do not penalize a clearly labelled source-backed finding merely because runtime was unavailable.

Return the schema response with concise reasons and case-relative evidence paths. Review all cases.
You have eight minutes. Preserve uncertainty where artifacts do not establish the answer.
''')
    study.write_json(out/'condition-map.json',mapping)


def run_batch(source,batch):
    cmd=study.cli(source,batch,batch/'review.json',batch/'schema.json')
    cmd[cmd.index('danger-full-access')]='workspace-write'
    started=time.monotonic()
    with open(batch/'events.jsonl','w') as log,open(batch/'stderr.txt','w') as err:
        try:
            result=subprocess.run(cmd,input='Read TASK.md and perform the artifact review.\n',text=True,cwd=batch,
                                  stdout=log,stderr=err,timeout=510)
            code=result.returncode
        except subprocess.TimeoutExpired:
            code='timeout'
    result={'batch':batch.name,'exit_code':code,'seconds':round(time.monotonic()-started,2)}
    study.write_json(batch/'review-status.json',result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','run'])
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();source=args.source.resolve();out=args.out.resolve()
    if args.command=='prepare':prepare(source,out)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda batch:run_batch(source,batch),sorted(out.glob('batch-*'))))
