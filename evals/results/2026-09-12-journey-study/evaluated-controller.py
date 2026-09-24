#!/usr/bin/env python3
"""Controller for a frozen, three-condition screening study. Never give to candidates."""
import argparse
import concurrent.futures
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def mutate(folder, surface):
    edits = {
        'api': [('domain.py', 'amount > row["paid"] - row["refunded"]', 'amount > row["paid"]'),
                ('domain.py', 'version != row["version"]', 'version > row["version"]'),
                ('domain.py', '            selected.append(row)', '            row["service"] = service\n            selected.append(row)')],
        'ui': [('static/app.js', '  if (token !== generation) return;\n', ''),
               ('static/app.js', "  if (!response.ok) {\n    el('feedback').textContent = row.error;\n    el('save').disabled = false;\n    return;\n  }\n", ''),
               ('static/index.html', '<button id="express" type="button" disabled>Use express delivery</button>',
                '<div id="express" role="button">Use express delivery</div>')]
    }
    for relative, before, after in edits[surface]:
        file = folder / relative
        content = file.read_text()
        assert content.count(before) == 1, relative
        file.write_text(content.replace(before, after))


def start_server(app, control):
    ready = control / 'ready.json'
    log = open(control / 'server.log', 'w')
    proc = subprocess.Popen([sys.executable, str(app / 'app.py'), '--ready', str(ready),
                             '--audit', str(control / 'audit.jsonl')], stdout=log, stderr=log)
    log.close()
    for _ in range(100):
        if ready.exists():
            return proc, json.loads(ready.read_text())['url']
        if proc.poll() is not None:
            raise RuntimeError((control / 'server.log').read_text())
        time.sleep(.05)
    proc.terminate()
    raise TimeoutError('Fixture did not become ready')


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(HERE / 'app', out / 'frozen-app', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT / 'skills', out / 'frozen-skills')
    shutil.copy2(HERE / 'protocol.md', out / 'protocol.md')
    shutil.copy2(HERE / 'template.md', out / 'template.md')
    skills = []
    for base in [Path.home()/'.codex/skills', Path.home()/'.agents/skills', Path.home()/'.codex/plugins/cache']:
        if base.exists():
            for file in base.rglob('SKILL.md'):
                # Tool documentation stays available equally; testing workflow skills are supplied only by the treatment.
                if file.parent.name == 'playwright-cli':
                    continue
                skills.extend([{'path': str(file), 'enabled': False}, {'path': str(file.parent), 'enabled': False}])
    config = 'skills.config=[' + ','.join('{path='+json.dumps(s['path'])+',enabled=false}' for s in skills) + ']'
    (out / 'skill-overrides.txt').write_text(config)
    # All six permutations appear across the eight blocks, balancing first/last positions closely.
    permutations = list(itertools.permutations(['normal', 'template', 'skill']))
    blocks = [(surface, variant, repeat) for repeat in (1, 2)
              for surface, variant in [('api', 'defects'), ('ui', 'control'), ('ui', 'defects'), ('api', 'control')]]
    schedule = []
    for index, (surface, variant, repeat) in enumerate(blocks):
        for condition in permutations[index % len(permutations)]:
            schedule.append({'id': f'run-{len(schedule)+1:02}', 'surface': surface,
                             'variant': variant, 'repeat': repeat, 'condition': condition})
    write_json(out / 'schedule.json', schedule)
    write_json(out / 'freeze.json', {'created_at': time.time(), 'model': 'gpt-6-astra', 'effort': 'high',
        'codex': subprocess.check_output([shutil.which('codex'), '--version'], text=True).strip(),
        'playwright_cli': subprocess.check_output(['playwright-cli', '--version'], text=True).strip(),
        'inputs': hashes(out), 'controller_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


def run_one(out, spec):
    run = out / spec['id']
    run.mkdir(exist_ok=False)
    candidate, control = run / 'candidate', run / 'controller'
    candidate.mkdir(); control.mkdir(); (candidate / 'evidence').mkdir()
    shutil.copytree(out / 'frozen-app', candidate / 'app')
    if spec['variant'] == 'defects':
        mutate(candidate / 'app', spec['surface'])
    surface = spec['surface']
    extra = ''
    if spec['condition'] == 'template':
        shutil.copy2(out / 'template.md', candidate / 'REPORT-TEMPLATE.md')
        extra = 'Use REPORT-TEMPLATE.md to structure the report.\n'
    elif spec['condition'] == 'skill':
        shutil.copytree(out / 'frozen-skills' / f'{surface}-exploratory-testing', candidate / 'skill')
        extra = 'Read and use skill/SKILL.md and the relevant linked references for this assessment.\n'
    server, url = start_server(candidate / 'app', control)
    session = 'journey-' + spec['id']
    task = f'''Assess Dispatch Desk's {'administrative API operations' if surface == 'api' else 'customer browser journey'} for release readiness.
The source, existing tests and business requirements are in app/. Runtime: {url}.
Investigate the risks you consider important and give the team an actionable assessment.
{extra}
Use only this candidate directory and this assigned loopback runtime. Do not inspect
parent directories, other runs, controller files or external copies of the application.
Do not change the supplied source, tests, requirements or guidance. Local scripts and
evidence files are allowed. No external services, issue filing, product fixes or delegation.
Fixture data changes are authorized within app/requirements.md. The controller resets
this instance afterwards. Close only the browser session you create.
Documentation-only defects are excluded. Work in English.

Tools: Python 3, curl and Playwright CLI are available. For browser work use
playwright-cli -s={session}; use its --help for syntax as needed. All browser traffic
must stay on this runtime. Use source and browser/HTTP tools as your assessment needs.
You have six minutes total, including reporting, up to 120 /api requests and 80 browser
actions. Check elapsed time yourself; reserve time to save your work. Save report.md
and any supporting evidence under evidence/. No particular report schema is required.
'''
    (candidate / 'TASK.md').write_text(task)
    before = hashes(candidate / 'app')
    skill_before = hashes(candidate / 'skill') if (candidate / 'skill').exists() else None
    config = (out / 'skill-overrides.txt').read_text()
    cmd = [shutil.which('codex'), 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
           '-s', 'danger-full-access', '-c', 'model_reasoning_effort="high"', '-c', 'project_doc_max_bytes=0',
           '-c', 'features.apps=false', '-c', config, '-m', 'gpt-6-astra', '--json',
           '-C', str(candidate), '-o', str(control / 'final.txt'), '-']
    started = time.time()
    print(json.dumps({'event': 'started', **spec}), flush=True)
    status, code = 'completed', None
    try:
        with open(control / 'events.jsonl', 'w') as stdout, open(control / 'stderr.txt', 'w') as stderr:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                    cwd=candidate, start_new_session=True)
            try:
                proc.communicate(input=b'Read TASK.md and perform the assessment.\n', timeout=390)
                code = proc.returncode
                if code:
                    status = 'runner-error'
            except subprocess.TimeoutExpired:
                status = 'timeout'
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL); proc.wait()
                code = proc.returncode
    finally:
        server.terminate()
        server.wait(timeout=10)
        subprocess.run(['playwright-cli', '-s='+session, 'close'], cwd=candidate,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    elapsed = time.time() - started
    events = []
    for line in (control / 'events.jsonl').read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    usage = [e.get('usage') for e in events if e.get('type') == 'turn.completed']
    api = [json.loads(line) for line in (control / 'audit.jsonl').read_text().splitlines()
           if json.loads(line)['path'].startswith('/api/')] if (control / 'audit.jsonl').exists() else []
    result = {**spec, 'status': status, 'exit_code': code, 'elapsed_seconds': round(elapsed, 2),
              'report_exists': (candidate / 'report.md').exists(), 'api_requests': len(api),
              'usage': usage, 'app_preserved': hashes(candidate / 'app') == before,
              'skill_preserved': hashes(candidate / 'skill') == skill_before if skill_before else None,
              'source_hashes': before, 'task_sha256': hashlib.sha256(task.encode()).hexdigest()}
    write_json(control / 'result.json', result)
    print(json.dumps({'event': 'finished', **result}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.command == 'prepare':
        prepare(out)
        print(out)
    else:
        specs = json.loads((out / 'schedule.json').read_text())
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_one, out, spec) for spec in specs]
            results = [future.result() for future in futures]
        write_json(out / 'run-results.json', results)


if __name__ == '__main__':
    main()
