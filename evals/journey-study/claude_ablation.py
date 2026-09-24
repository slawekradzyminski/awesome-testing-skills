#!/usr/bin/env python3
"""Claude Opus 5.5 four-arm API ablation pilot. Evaluator-only; never give to candidates.

Development/calibration pilot on the known-ceiling Dispatch Desk API defective fixture.
It cannot establish skill superiority. See claude-ablation.md.
"""
import argparse
import concurrent.futures
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import urlsplit

import study  # reuses hashing, the frozen API seed mutation and fixture start-up; study.py is unchanged

HERE, ROOT = study.HERE, study.ROOT
SKILL = ROOT / 'skills' / 'api-exploratory-testing'
ARMS = ('normal', 'report-only', 'investigation-only', 'full')
# Williams square: across four blocks every arm occupies every position once and follows every other arm once.
WILLIAMS = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1))
MODEL, EFFORT = 'claude-opus-5-5', 'high'
TOOLS = 'Bash,Read,Write,Edit,Glob,Grep'  # no Agent/Task (delegation), WebFetch or WebSearch
TIME_BUDGET, HARD_STOP, API_BUDGET, MAX_BUDGET_USD = 360, 390, 120, '1.5'
STDIN_PROMPT = 'Read TASK.md and perform the assessment.\n'
SECTIONS = ('Establish the target and invite source access', 'Read code to find plausible failures',
            'Explore the running API', 'Evidence, findings, and completion')
INVESTIGATION, REPORTING = SECTIONS[:3], SECTIONS[3:]
# Fresh fixture state (must equal app/domain.py Desk().orders; checked by the unit test).
INITIAL_ORDERS = {
    'A100': {'id': 'A100', 'owner': 'alice', 'paid': 10000, 'refunded': 0, 'address': '10 Oak Street',
             'version': 1, 'note': 'Leave with reception', 'service': 'standard'},
    'A200': {'id': 'A200', 'owner': 'alice', 'paid': 6000, 'refunded': 0, 'address': '20 Pine Street',
             'version': 1, 'note': 'Ring twice', 'service': 'standard'},
    'B100': {'id': 'B100', 'owner': 'bob', 'paid': 4000, 'refunded': 0, 'address': '30 Elm Street',
             'version': 1, 'note': 'Side entrance', 'service': 'standard'}}
# Fields each accepted write is intended to change; other fields in its response are not trusted.
INTENDED = {'refund': ('refunded',), 'address': ('address', 'version'), 'note': ('note',)}

TASK = '''Assess Dispatch Desk's administrative API operations for release readiness.
The source, existing tests and business requirements are in app/. Runtime: {url}.
Investigate the risks you consider important and give the team an actionable assessment.
{extra}
Use only this candidate directory and this assigned loopback runtime. Do not inspect
parent directories, other runs, controller files or external copies of the application.
Do not change the supplied source, tests, requirements or guidance. Local scripts and
evidence files are allowed. No external services, issue filing, product fixes or delegation.
Fixture data changes are authorized within app/requirements.md. The controller resets
this instance afterwards. Documentation-only defects are excluded. Work in English.

Tools: Python 3 and curl are available. You have six minutes total, including reporting,
and up to 120 /api requests. Check elapsed time yourself; reserve time to save your work.
Save the report as evidence/report.md and any supporting evidence under evidence/.
No particular report schema is required.
'''
GUIDED = 'Read and use guidance/SKILL.md and the relevant linked references for this assessment.\n'


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


# ---------------------------------------------------------------- audit scorer

def _path(entry):
    return urlsplit(entry.get('path') or '').path.rstrip('/') or '/'


def _read_rows(entry):
    """Order rows exposed to the candidate by a successful GET (single order or list)."""
    if entry.get('method') != 'GET' or entry.get('status') != 200:
        return []
    path, value = _path(entry), entry.get('response')
    if not isinstance(value, dict):
        return []
    if path == '/api/orders':
        rows = value.get('orders')
        return [r for r in rows if isinstance(r, dict) and isinstance(r.get('id'), str)] if isinstance(rows, list) else []
    parts = path.split('/')
    if len(parts) == 4 and parts[1:3] == ['api', 'orders'] and value.get('id') == parts[3]:
        return [value]
    return []


def _num(value):
    return value if type(value) is int else None


def score_audit(entries, initial=INITIAL_ORDERS):
    """Score R1-R3 from the runtime audit request/response sequence (audit order = reply order).

    A seed counts as observed only when a successful follow-up read, after the violating
    request, shows the violated state. Triggering the write alone is recorded separately.
    Report text is never consulted. Entries that are not dicts (malformed lines) are skipped;
    reported line numbers are 1-based positions in ``entries``.
    """
    intended = deepcopy(initial)           # state implied by accepted writes' intended effects only
    history = {oid: {row['version']} for oid, row in initial.items()}  # versions each order really had
    accepted_refunds = {oid: 0 for oid in initial}
    over_refunds, stale_writes, rejected_batches = [], [], []
    result = {seed: {'triggered': False, 'observed': False, 'trigger_line': None, 'observation_line': None}
              for seed in ('R1', 'R2', 'R3')}

    def mark(seed, key, line):
        if not result[seed][key]:
            result[seed][key] = True
            result[seed]['trigger_line' if key == 'triggered' else 'observation_line'] = line

    for line, entry in enumerate(entries, 1):
        if not isinstance(entry, dict) or not _path(entry).startswith('/api/'):
            continue
        path, status, request, response = _path(entry), entry.get('status'), entry.get('request'), entry.get('response')
        if entry.get('method') == 'POST':
            parts = path.strip('/').split('/')
            if len(parts) == 4 and parts[:2] == ['api', 'orders'] and parts[3] in INTENDED:
                oid, op = parts[2], parts[3]
                if status != 200 or oid not in intended or not isinstance(response, dict) or response.get('id') != oid:
                    continue
                if op == 'refund':
                    accepted_refunds[oid] += 1
                    refunded, paid = _num(response.get('refunded')), _num(response.get('paid'))
                    if accepted_refunds[oid] >= 2 and refunded is not None and paid is not None and refunded > paid:
                        over_refunds.append((oid, line))
                        mark('R1', 'triggered', line)
                elif op == 'address' and isinstance(request, dict):
                    version, current = _num(request.get('version')), intended[oid]
                    if (version is not None and version in history[oid] and version < current['version']
                            and response.get('address') != current['address']):
                        stale_writes.append({'order': oid, 'line': line, 'stale': response.get('address'),
                                             'overwritten': current['address']})
                        mark('R2', 'triggered', line)
                    if _num(response.get('version')) is not None:
                        history[oid].add(response['version'])
                for field in INTENDED[op]:
                    if field in response:
                        intended[oid][field] = response[field]
            elif path == '/api/services' and isinstance(request, dict):
                ids, service = request.get('ids'), request.get('service')
                if status == 200 and isinstance(response, dict):
                    for row in response.get('orders') or []:
                        if isinstance(row, dict) and row.get('id') in intended and 'service' in row:
                            intended[row['id']]['service'] = row['service']
                elif isinstance(status, int) and status >= 400 and isinstance(ids, list) and service in ('standard', 'express'):
                    earlier, blocked = [], False
                    for oid in ids:
                        row = intended.get(oid) if isinstance(oid, str) else None
                        if row is None or row['owner'] != entry.get('actor'):
                            blocked = True  # first missing or forbidden order ends the accessible prefix
                            break
                        earlier.append(oid)
                    changed = [oid for oid in earlier if intended[oid]['service'] != service] if blocked else []
                    if changed:  # rejected batch whose accessible prefix would change: the exposing request
                        rejected_batches.append({'line': line, 'service': service, 'orders': changed})
                        mark('R3', 'triggered', line)
        for row in _read_rows(entry):
            oid = row['id']
            if oid not in intended:
                continue
            refunded, paid = _num(row.get('refunded')), _num(row.get('paid'))
            if (any(o == oid for o, _ in over_refunds) and refunded is not None and paid is not None
                    and refunded > paid):
                mark('R1', 'observed', line)
            if any(w['order'] == oid and row.get('address') == w['stale'] != w['overwritten'] for w in stale_writes):
                mark('R2', 'observed', line)
            for batch in rejected_batches:
                if (oid in batch['orders'] and row.get('service') == batch['service']
                        and intended[oid]['service'] != batch['service']):
                    mark('R3', 'observed', line)
    result['observed_count'] = sum(result[s]['observed'] for s in ('R1', 'R2', 'R3'))
    result['triggered_count'] = sum(result[s]['triggered'] for s in ('R1', 'R2', 'R3'))
    return result


def load_audit(path):
    entries = []
    if Path(path).exists():
        for text in Path(path).read_text().splitlines():
            try:
                entries.append(json.loads(text))
            except json.JSONDecodeError:
                entries.append(None)
    return entries


# ---------------------------------------------------------------- freezing

def split_skill(text):
    assert text.startswith('---\n'), 'skill frontmatter expected'
    body = text.split('---\n', 2)[2].lstrip('\n')
    head, *chunks = re.split(r'(?m)^## ', body)
    sections = {c.partition('\n')[0].strip(): '## ' + c.rstrip('\n') + '\n' for c in chunks}
    assert tuple(sections) == SECTIONS, f'unexpected skill sections: {list(sections)}'
    return head.rstrip('\n') + '\n', sections


def build_arms(arms_dir):
    """Write each arm's frozen task template and guidance directory; return their hashes."""
    head, sections = split_skill((SKILL / 'SKILL.md').read_text())
    parts = {'report-only': (REPORTING, 'reporting.md'), 'investigation-only': (INVESTIGATION, 'experiment-design.md')}
    for arm in ARMS:
        folder = arms_dir / arm
        folder.mkdir(parents=True)
        guidance = folder / 'guidance'
        if arm == 'full':
            shutil.copytree(SKILL, guidance, ignore=shutil.ignore_patterns('__pycache__'))
        elif arm in parts:
            names, reference = parts[arm]
            (guidance / 'references').mkdir(parents=True)
            (guidance / 'SKILL.md').write_text(head + ''.join('\n' + sections[n] for n in names))
            shutil.copy2(SKILL / 'references' / reference, guidance / 'references' / reference)
        if guidance.exists():
            for link in re.findall(r'\]\((references/[^)#]+)', (guidance / 'SKILL.md').read_text()):
                assert (guidance / link).is_file(), f'{arm}: unresolved link {link}'
        (folder / 'TASK.template.md').write_text(TASK.replace('{extra}', '' if arm == 'normal' else GUIDED))
    return {arm: {'task_template_sha256': sha((arms_dir / arm / 'TASK.template.md').read_bytes()),
                  'guidance': study.hashes(arms_dir / arm / 'guidance') if (arms_dir / arm / 'guidance').exists() else {}}
            for arm in ARMS}


def git_state():
    def git(*args):
        return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True).stdout.rstrip('\n')
    return {'revision': git('rev-parse', 'HEAD'),
            'uncommitted': git('status', '--porcelain', '--', 'skills/api-exploratory-testing', 'evals/journey-study').splitlines()}


def prepare(out, repeats, model, max_budget):
    if repeats < 1:
        raise ValueError('At least one schedule block is required')
    if out.is_relative_to(ROOT):
        raise SystemExit('Use an output directory outside the repository so candidates do not inherit it.')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(HERE / 'app', out / 'frozen-app', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(HERE / 'claude-ablation.md', out / 'claude-ablation.md')
    arms = build_arms(out / 'arms')
    schedule = []
    for block in range(repeats):
        for position, index in enumerate(WILLIAMS[block % 4]):
            schedule.append({'id': f'run-{len(schedule)+1:02}', 'block': block + 1,
                             'position': position + 1, 'arm': ARMS[index]})
    study.write_json(out / 'schedule.json', schedule)
    claude = shutil.which('claude')
    study.write_json(out / 'freeze.json', {
        'created_at': time.time(), 'purpose': 'development/calibration pilot; cannot establish skill superiority',
        'surface': 'api', 'variant': 'defects', 'model_requested': model, 'effort': EFFORT, 'tools': TOOLS,
        'max_budget_usd': max_budget, 'time_budget_seconds': TIME_BUDGET, 'hard_stop_seconds': HARD_STOP,
        'api_request_budget': API_BUDGET, 'stdin_prompt_sha256': sha(STDIN_PROMPT),
        'claude_code': subprocess.check_output([claude, '--version'], text=True).strip() if claude else None,
        'python': sys.version, 'git': git_state(), 'arms': arms,
        'controller_sha256': sha(Path(__file__).read_bytes()), 'study_py_sha256': sha((HERE / 'study.py').read_bytes()),
        'inputs': study.hashes(out)})


# ---------------------------------------------------------------- runner

def candidate_env(control):
    """Inherited environment minus Claude/Anthropic overrides; API key auth and a fresh config dir."""
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith('CLAUDE') or (k.startswith('ANTHROPIC_') and k != 'ANTHROPIC_API_KEY'))}
    removed = sorted(set(os.environ) - set(env))
    env['CLAUDE_CONFIG_DIR'] = str(control / 'claude-config')  # no user skills, agents, settings or memory
    (control / 'claude-config').mkdir()
    return env, removed


def boundary_flags(events, out, candidate):
    """Heuristic: tool inputs naming controller/repository paths outside the candidate directory."""
    forbidden = [str(out), str(ROOT), str(Path.home() / '.claude')]
    flags, tools = [], {}
    for index, event in enumerate(events):
        content = (event.get('message') or {}).get('content') if event.get('type') == 'assistant' else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                tools[block.get('name')] = tools.get(block.get('name'), 0) + 1
                text = json.dumps(block.get('input')).replace(str(candidate), '<candidate>')
                hits = [f for f in forbidden if f in text]
                if hits or '../' in text:
                    flags.append({'event': index, 'tool': block.get('name'), 'paths': hits, 'parent_reference': '../' in text})
    return tools, flags


def run_one(out, spec, freeze):
    run = out / spec['id']
    run.mkdir(exist_ok=False)
    candidate, control = run / 'candidate', run / 'controller'
    candidate.mkdir(); control.mkdir(); (candidate / 'evidence').mkdir()
    shutil.copytree(out / 'frozen-app', candidate / 'app')
    study.mutate(candidate / 'app', 'api')
    arm_dir = out / 'arms' / spec['arm']
    if (arm_dir / 'guidance').exists():
        shutil.copytree(arm_dir / 'guidance', candidate / 'guidance')
    server, url = study.start_server(candidate / 'app', control)
    task = (arm_dir / 'TASK.template.md').read_text().replace('{url}', url)
    (candidate / 'TASK.md').write_text(task)
    app_before = study.hashes(candidate / 'app')
    guidance_before = study.hashes(candidate / 'guidance') if (candidate / 'guidance').exists() else None
    env, removed_env = candidate_env(control)
    cmd = [shutil.which('claude'), '-p', '--bare', '--model', freeze['model_requested'], '--effort', EFFORT,
           '--tools', TOOLS, '--disable-slash-commands', '--strict-mcp-config', '--no-session-persistence',
           '--dangerously-skip-permissions', '--max-budget-usd', freeze['max_budget_usd'],
           '--output-format', 'stream-json', '--verbose']
    started = time.time()
    print(json.dumps({'event': 'started', **spec}), flush=True)
    status, code, fixture_alive = 'completed', None, None
    try:
        with open(control / 'events.jsonl', 'w') as stdout, open(control / 'stderr.txt', 'w') as stderr:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                    cwd=candidate, env=env, start_new_session=True)
            try:
                proc.communicate(input=STDIN_PROMPT.encode(), timeout=HARD_STOP)
                code = proc.returncode
                status = 'runner-error' if code else status
            except subprocess.TimeoutExpired:
                status = 'timeout'
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL); proc.wait()
                code = proc.returncode
    finally:
        fixture_alive = server.poll() is None
        server.terminate()
        server.wait(timeout=10)
    elapsed = time.time() - started
    events = []
    for text in (control / 'events.jsonl').read_text().splitlines():
        try:
            events.append(json.loads(text))
        except json.JSONDecodeError:
            pass
    init = next((e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init'), {})
    final = next((e for e in reversed(events) if e.get('type') == 'result'), None)
    if final is None and status == 'completed':
        status = 'missing-result'
    elif final is not None and status == 'completed' and (final.get('is_error') or final.get('subtype') != 'success'):
        status = f"runner-{final.get('subtype') or 'error'}"
    if final is not None and isinstance(final.get('result'), str):
        (control / 'final.txt').write_text(final['result'])
    resolved = sorted((final or {}).get('modelUsage') or {})
    audit = load_audit(control / 'audit.jsonl')
    api = [e for e in audit if isinstance(e, dict) and _path(e).startswith('/api/')]
    report = candidate / 'evidence' / 'report.md'
    tools, flags = boundary_flags(events, out, candidate)
    result = {
        **spec, 'surface': 'api', 'variant': 'defects', 'status': status, 'exit_code': code,
        'fixture_alive_at_end': fixture_alive, 'elapsed_seconds': round(elapsed, 2),
        'over_time_budget': elapsed > TIME_BUDGET,
        'model': {'requested': freeze['model_requested'], 'init_reported': init.get('model'), 'usage_models': resolved,
                  'mismatch': bool(resolved) and not all(m.startswith(freeze['model_requested']) for m in resolved),
                  'claude_code': init.get('claude_code_version') or freeze['claude_code']},
        'cost_usd_estimate': (final or {}).get('total_cost_usd'), 'usage': (final or {}).get('usage'),
        'model_usage': (final or {}).get('modelUsage'), 'num_turns': (final or {}).get('num_turns'),
        'duration_ms': (final or {}).get('duration_ms'), 'duration_api_ms': (final or {}).get('duration_api_ms'),
        'session': {k: init.get(k) for k in ('tools', 'mcp_servers', 'slash_commands', 'skills', 'agents',
                                             'apiKeySource', 'permissionMode')},
        'tool_calls': tools, 'boundary_flags': flags, 'removed_env_names': removed_env,
        'prompt': {'task_sha256': sha(task), 'task_template_sha256': freeze['arms'][spec['arm']]['task_template_sha256'],
                   'stdin_sha256': sha(STDIN_PROMPT), 'guidance_sha256': sha(json.dumps(guidance_before, sort_keys=True))},
        'command': [Path(cmd[0]).name, *cmd[1:]],
        'audit': {'api_requests': len(api), 'over_request_budget': len(api) > API_BUDGET,
                  'malformed_lines': sum(e is None for e in audit),
                  'statuses': {str(s): sum(e.get('status') == s for e in api) for s in sorted({e.get('status') for e in api}, key=str)}},
        'app_preserved': study.hashes(candidate / 'app') == app_before,
        'guidance_preserved': study.hashes(candidate / 'guidance') == guidance_before if guidance_before else None,
        'source_hashes': app_before,
        'report': {'path': 'candidate/evidence/report.md', 'exists': report.is_file(),
                   'sha256': sha(report.read_bytes()) if report.is_file() else None,
                   'bytes': report.stat().st_size if report.is_file() else 0},
        'score': score_audit(audit)}
    study.write_json(control / 'result.json', result)
    print(json.dumps({'event': 'finished', 'id': spec['id'], 'arm': spec['arm'], 'status': status,
                      'observed': result['score']['observed_count']}), flush=True)
    return result


def run(out, workers):
    freeze = json.loads((out / 'freeze.json').read_text())
    current = study.hashes(out)
    changed = sorted(k for k, v in freeze['inputs'].items() if current.get(k) != v)
    if changed or sha(Path(__file__).read_bytes()) != freeze['controller_sha256']:
        raise SystemExit(f'Frozen inputs or controller changed since prepare: {changed or ["claude_ablation.py"]}')
    if not os.environ.get('ANTHROPIC_API_KEY'):
        raise SystemExit('ANTHROPIC_API_KEY is required (--bare uses API-key authentication only).')
    specs = json.loads((out / 'schedule.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda spec: run_one(out, spec, freeze), specs))
    study.write_json(out / 'run-results.json', results)
    # Descriptive only: per-run observed counts by arm, no pooled statistics or superiority claim.
    study.write_json(out / 'arm-summary.json', {arm: [{'id': r['id'], 'status': r['status'],
        'observed': r['score']['observed_count'], 'cost_usd_estimate': r['cost_usd_estimate']}
        for r in results if r['arm'] == arm] for arm in ARMS})


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('command', choices=['prepare', 'run', 'score'])
    parser.add_argument('--out', type=Path, help='fresh pilot directory (prepare/run)')
    parser.add_argument('--audit', type=Path, help='audit.jsonl to rescore (score)')
    parser.add_argument('--repeats', type=int, default=2, help='Williams blocks of four runs (4 = fully balanced)')
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--max-budget-usd', default=MAX_BUDGET_USD)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    if args.command == 'score':
        print(json.dumps(score_audit(load_audit(args.audit)), indent=2))
    elif args.command == 'prepare':
        prepare(args.out.resolve(), args.repeats, args.model, args.max_budget_usd)
        print(args.out.resolve())
    else:
        run(args.out.resolve(), args.workers)


if __name__ == '__main__':
    main()
