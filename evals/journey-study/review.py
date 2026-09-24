#!/usr/bin/env python3
"""Prepare condition-masked artifact review after runs; keep mapping evaluator-only."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import random
import shutil
import subprocess
import time
import study


def prepare(source, out):
    out.mkdir(parents=True, exist_ok=False)
    specs = json.loads((source / 'schedule.json').read_text())
    random.Random(20260912).shuffle(specs)
    mapping = {}
    schema = {'type': 'object', 'additionalProperties': False, 'required': ['reviews'], 'properties': {
      'reviews': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
        'required': ['case_id', 'seeded', 'additional', 'coverage_score', 'coverage_reason', 'integrity_notes', 'reviewed_evidence'],
        'properties': {
          'case_id': {'type': 'string'},
          'seeded': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['id', 'identified', 'actionable', 'impact_point', 'severity_point', 'acceptance_point', 'reason', 'evidence'],
            'properties': {'id': {'type': 'string'}, 'identified': {'type': 'boolean'}, 'actionable': {'type': 'boolean'},
              'impact_point': {'type': 'integer'}, 'severity_point': {'type': 'integer'}, 'acceptance_point': {'type': 'integer'},
              'reason': {'type': 'string'}, 'evidence': {'type': 'array', 'items': {'type': 'string'}}}}},
          'additional': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['title', 'classification', 'impact_point', 'severity_point', 'acceptance_point', 'reason', 'evidence'],
            'properties': {'title': {'type': 'string'}, 'classification': {'type': 'string', 'enum': ['valid', 'unsupported', 'unresolved', 'out-of-scope']},
              'impact_point': {'type': 'integer'}, 'severity_point': {'type': 'integer'}, 'acceptance_point': {'type': 'integer'},
              'reason': {'type': 'string'}, 'evidence': {'type': 'array', 'items': {'type': 'string'}}}}},
          'coverage_score': {'type': 'integer'}, 'coverage_reason': {'type': 'string'},
          'integrity_notes': {'type': 'array', 'items': {'type': 'string'}},
          'reviewed_evidence': {'type': 'array', 'items': {'type': 'string'}}}}}}}
    for batch in range(6):
        folder = out / f'batch-{batch+1}'
        folder.mkdir()
        entries = []
        for index, spec in enumerate(specs[batch*4:batch*4+4], batch*4+1):
            case_id = f'case-{index:02}'
            mapping[case_id] = spec
            original = source / spec['id']
            case = folder / case_id
            shutil.copytree(original / 'candidate', case, ignore=shutil.ignore_patterns('skill', 'TASK.md', 'REPORT-TEMPLATE.md', '__pycache__', '.playwright-cli'))
            # Preserve report/evidence as written; exact local paths become portable case paths.
            for file in case.rglob('*'):
                if file.is_file() and file.suffix in ('.md', '.txt', '.json', '.jsonl', '.py', '.js'):
                    text = file.read_text()
                    text = text.replace(str(original / 'candidate'), str(case))
                    file.write_text(text)
            if (original / 'controller/audit.jsonl').exists():
                shutil.copy2(original / 'controller/audit.jsonl', case / 'controller-audit.jsonl')
            else:
                (case / 'controller-audit.jsonl').write_text('')
            result = json.loads((original / 'controller/result.json').read_text())
            report = 'report.md' if (case / 'report.md').exists() else 'evidence/report.md' if (case / 'evidence/report.md').exists() else None
            entries.append({'case_id': case_id, 'surface': spec['surface'], 'report_path': report,
                'expected_seeds': (['R1','R2','R3'] if spec['surface']=='api' else ['U1','U2','U3']) if spec['variant']=='defects' else [],
                'runtime_status': result['status'], 'source_preserved': result['app_preserved'],
                'elapsed_seconds': result['elapsed_seconds'], 'api_requests': result['api_requests']})
        study.write_json(folder / 'cases.json', entries)
        protocol = (source / 'protocol.md').read_text()
        start = protocol.index('## Evaluator-only expected observations')
        end = protocol.index('## Interpretation fixed in advance')
        (folder / 'RUBRIC.md').write_text(protocol[start:end])
        (folder / 'TASK.md').write_text('''Review the four exploratory-testing reports described in cases.json against RUBRIC.md.
Work only in this batch directory; do not inspect parents, other batches or external applications.
Do not run the application, reproduction scripts or network tools. Inspect each actual report,
its decisive retained evidence, relevant source/requirements and supplied server audit.
Open the screenshots relevant to visual claims. A controller audit can corroborate a claim
but cannot replace reproduction evidence missing from the candidate's own artifacts.

Condition labels are withheld. Do not infer or score the experimental condition. Some report
wording may reveal guidance use; judge actual evidence, not style, formatting or report length.
Find report.md at the case root or inside evidence/: the shared task's output-location wording
was ambiguous, so either is acceptable. Resolve links relative to the actual report location;
record genuinely missing/broken evidence separately. Do not fabricate unperformed verification.

Score every expected seed, including missed ones. Each impact/severity/acceptance point is 0 or 1;
award points only for substantiated findings. Coverage is 0, 1 or 2 as defined in the rubric.
For every additional confirmed claim, distinguish valid, unsupported, unresolved or out-of-scope.
Apply the same three triage points to valid additional findings; use zero for unsubstantiated claims.
Do not count suggestions or qualified untested risks as false-positive bug reports. A corrected
variant has no seeded faults but can contain real additional defects. Controlled response timing
or aborted requests may establish conditional client-handling failures if honestly disclosed;
they do not prove spontaneous network failures. Explain any ambiguity in the expected behavior.

Return the structured review required by the output schema. Keep reasons concise and cite
specific case-relative evidence files and decisive observations. You have eight minutes.
''')
        study.write_json(folder / 'schema.json', schema)
    study.write_json(out / 'condition-map.json', mapping)


def run_batch(source, batch):
    cmd = [shutil.which('codex'), 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
           '-s', 'workspace-write', '-c', 'project_doc_max_bytes=0', '-c', 'features.apps=false',
           '-c', 'model_reasoning_effort="high"', '-c', (source / 'skill-overrides.txt').read_text(),
           '-m', 'gpt-6-astra', '--json', '-C', str(batch), '--output-schema', str(batch/'schema.json'),
           '-o', str(batch/'review.json'), '-']
    start=time.time()
    with open(batch/'review-events.jsonl','w') as stdout, open(batch/'review-stderr.txt','w') as stderr:
        result = subprocess.run(cmd, input='Read TASK.md and perform the artifact review.\n',text=True,
                                stdout=stdout,stderr=stderr,cwd=batch,timeout=540)
    print(json.dumps({'batch': batch.name, 'exit_code': result.returncode, 'seconds': round(time.time()-start)}),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','run'])
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='prepare':
        prepare(args.source.resolve(),args.out.resolve())
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda batch: run_batch(args.source.resolve(),batch), sorted(args.out.resolve().glob('batch-*'))))
