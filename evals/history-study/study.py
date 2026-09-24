"""Frozen real-project evaluation controller. Never expose to candidates."""
import argparse
import concurrent.futures
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import threading
import time
from runtime import Runtime, CUSTOMER

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXCLUDED = {'.git', '.github', '.codex', '.claude', '.agents', 'node_modules', 'target', 'dist', '__pycache__'}
LEGACY_PORTS=threading.Lock()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def hashes(folder):
    return {str(f.relative_to(folder)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(folder.rglob('*')) if f.is_file()
            and not any(p in EXCLUDED for p in f.relative_to(folder).parts)}


def preserved(folder, before):
    return all((folder/p).is_file() and hashlib.sha256((folder/p).read_bytes()).hexdigest()==h for p,h in before.items())


def archive(repo, ref, dest):
    raw = subprocess.check_output(['git','archive',ref],cwd=repo)
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        members = [m for m in tar.getmembers() if not any(p in EXCLUDED for p in Path(m.name).parts)
                   and Path(m.name).name not in ('AGENTS.md','CLAUDE.md')]
        tar.extractall(dest,members=members,filter='data')
    return hashlib.sha256(raw).hexdigest()


def skill_config():
    disabled=[]
    for base in [Path.home()/'.codex/skills',Path.home()/'.agents/skills',Path.home()/'.codex/plugins/cache']:
        if base.exists():
            for file in base.rglob('SKILL.md'):
                if file.parent.name != 'playwright-cli':
                    disabled.extend([str(file),str(file.parent)])
    return 'skills.config=['+','.join('{path='+json.dumps(p)+',enabled=false}' for p in sorted(set(disabled)))+']'


def cli(out, cwd, output, schema=None):
    cmd=[shutil.which('codex'),'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check',
         '-s','danger-full-access','-c','project_doc_max_bytes=0','-c','features.apps=false',
         '-c','model_reasoning_effort="high"','-c',(out/'skill-overrides.txt').read_text(),
         '-m','gpt-6-astra','--json','-C',str(cwd),'-o',str(output)]
    if schema:
        cmd += ['--output-schema',str(schema)]
    return cmd+['-']


def prepare(out, build, backend_repo=None, frontend_repo=None):
    required = ['api-before','api-fixed','runtime-backend','ui-before','ui-fixed',
                'mobile-before','mobile-fixed','cart-before','cart-fixed']
    missing = []
    for label in required:
        folder = build / label
        ready = (any((folder / 'target').glob('*.jar')) if label in required[:3]
                 else (folder / 'dist' / 'index.html').is_file())
        if not ready:
            missing.append(label)
    if missing:
        raise FileNotFoundError('Missing compiled historical artifacts: ' + ', '.join(missing))
    out.mkdir(parents=True,exist_ok=False)
    cases=json.loads((HERE/'cases.json').read_text())
    sources=json.loads((HERE/'sources.json').read_text())
    for name,source in sources.items():
        override=backend_repo if source['url'].endswith('/test-secure-backend') else frontend_repo
        if override:
            source['repository']=str(override.resolve())
        source['archive_sha256']=archive(source['repository'],source['revision'],out/'sources'/name)
        source['file_hashes']=hashes(out/'sources'/name)
    write_json(out/'sources.json',sources)
    write_json(out/'cases.json',cases)
    shutil.copytree(ROOT/'skills',out/'skills')
    for file in ['protocol.md','template.md','study.py','runtime.py','review.py','aggregate.py']:
        shutil.copy2(HERE/file,out/file)
    (out/'skill-overrides.txt').write_text(skill_config())
    permutations=list(itertools.permutations(['normal','template','skill']))
    schedule=[]
    for block,(repeat,case) in enumerate((r,c) for r in [1,2] for c in cases):
        for arm in permutations[block%6]:
            schedule.append({'id':f'run-{len(schedule)+1:02}', 'case_id':case['id'],
                             'condition':arm,'repeat':repeat,'surface':case['surface'],'group':case['group']})
    write_json(out/'schedule.json',schedule)
    compiled={}
    for label in ['api-before','api-fixed','runtime-backend','ui-before','ui-fixed','mobile-before','mobile-fixed','cart-before','cart-fixed']:
        compiled[label]=({str(f.relative_to(build/label)):hashlib.sha256(f.read_bytes()).hexdigest()
                          for f in sorted((build/label/'dist').rglob('*')) if f.is_file()} if (build/label/'dist').exists()
                         else {str(f.relative_to(build/label)):hashlib.sha256(f.read_bytes()).hexdigest()
                               for f in sorted((build/label/'target').glob('*.jar'))})
    if (build/'runtime-tools.json').exists():
        shutil.copy2(build/'runtime-tools.json',out/'runtime-tools.json')
    write_json(out/'freeze.json',{'created_at':time.time(),'model':'gpt-6-astra','effort':'high',
        'codex':subprocess.check_output([shutil.which('codex'),'--version'],text=True).strip(),
        'playwright_cli':subprocess.check_output(['playwright-cli','--version'],text=True).strip(),
        'build_root':str(build),'compiled_hashes':compiled,'input_hashes':hashes(out)})
    print(out,flush=True)


def task_text(case, runtime_url, session, condition):
    extra=''
    if condition=='template':
        extra='Use REPORT-TEMPLATE.md for the report.\n'
    elif condition=='skill':
        extra='Read and use skill/SKILL.md and relevant linked references.\n'
    source='Project source and its original documentation are in app/.' if case.get('sources') else 'Project source is not available for this session.'
    if case.get('legacy'):
        source += ' The assigned API origin is also http://localhost:4001; this historical UI uses that origin.'
    fixture=('Disposable customer login: '+CUSTOMER['username']+' / '+CUSTOMER['password']+'.\n'
             'The instance has a small catalog and this customer already has a cart.\n'
             'You may change this customer\'s cart and create orders in this isolated instance.\n'
             'Catalog administration, account administration and external delivery are outside scope.\n'
             'This is a test gateway with controlled latency; latency itself has no performance SLA.\n'
             'Images/external links and optional email, SSO, LLM and traffic services are outside this setup.\n'
             if case['surface']=='ui' else
             'The instance is disposable. You may register test accounts, sign in and change your own account data.\n'
             'Do not send email, use external providers or exercise catalog/order/LLM administration.\n')
    return f'''{case['task']}
{source}
Test instance: {runtime_url}
{fixture}{extra}
Use only this directory and the assigned test instance. Do not inspect parent directories,
other runs, controller files, Git history or remote copies. Do not alter supplied application
source, tests or guidance, start another application, fix product code, file issues or delegate.
Documentation-only defects are excluded. Work in English.

Python, curl, Java, Node and Playwright CLI are available. For browser work use
playwright-cli -s={session}; consult its help as needed. All application traffic must stay
on the assigned instance. Close only your browser session; the owner discards the database.
You have eight minutes including reporting, up to 180 API requests and 100 browser actions.
Write your assessment to report.md at this directory's root; supporting files belong in evidence/.
No particular report format is required.
'''


def run_one(out, spec):
    case=next(c for c in json.loads((out/'cases.json').read_text()) if c['id']==spec['case_id'])
    build=Path(json.loads((out/'freeze.json').read_text())['build_root'])
    folder=out/spec['id'];folder.mkdir(exist_ok=False)
    candidate,control=folder/'candidate',folder/'controller'
    candidate.mkdir();control.mkdir();(candidate/'evidence').mkdir()
    for destination,source in case.get('sources',{}).items():
        shutil.copytree(out/'sources'/source,candidate/'app'/destination)
    if spec['condition']=='skill':
        shutil.copytree(out/'skills'/f"{case['surface']}-exploratory-testing",candidate/'skill')
    elif spec['condition']=='template':
        shutil.copy2(out/'template.md',candidate/'REPORT-TEMPLATE.md')
    before=hashes(candidate/'app') if (candidate/'app').exists() else {}
    skill_before=hashes(candidate/'skill') if (candidate/'skill').exists() else None
    session='history-'+spec['id']
    result={**spec,'status':'infrastructure-error','exit_code':None,'elapsed_seconds':0,'usage':[],
            'report_path':None,'api_requests':0,'mutation_requests':0,'source_preserved':True,'skill_preserved':None}
    runtime=Runtime(build,control,backend=case['backend'],frontend=case.get('frontend'),outage=case.get('outage',False))
    setup_start=time.monotonic()
    print(json.dumps({'event':'starting',**spec}),flush=True)
    if case.get('legacy'):
        LEGACY_PORTS.acquire()
    try:
        runtime.start()
        result['startup_seconds']=round(time.monotonic()-setup_start,2)
        task=task_text(case,runtime.url,session,spec['condition'])
        (candidate/'TASK.md').write_text(task)
        result['task_sha256']=hashlib.sha256(task.encode()).hexdigest()
        result['url']=runtime.url
        started=time.monotonic()
        with open(control/'events.jsonl','w') as log,open(control/'stderr.txt','w') as err:
            proc=subprocess.Popen(cli(out,candidate,control/'final.txt'),cwd=candidate,stdin=subprocess.PIPE,
                                  stdout=log,stderr=err,start_new_session=True)
            try:
                proc.communicate(input=b'Read TASK.md and perform the assessment.\n',timeout=480)
                result['exit_code']=proc.returncode
                result['status']='completed' if proc.returncode==0 else 'runner-error'
            except subprocess.TimeoutExpired:
                result['status']='timeout'
                os.killpg(proc.pid,signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                result['exit_code']=proc.returncode
        result['elapsed_seconds']=round(time.monotonic()-started,2)
    except Exception as exc:
        result['error']=type(exc).__name__+': '+str(exc)
    finally:
        cleanup=time.monotonic()
        runtime.stop()
        try:
            close=subprocess.run(['playwright-cli','-s='+session,'close'],cwd=candidate,
                                 capture_output=True,text=True,timeout=20)
            result['browser_close_exit_code']=close.returncode
            (control/'browser-close.txt').write_text(close.stdout+close.stderr)
        except subprocess.TimeoutExpired:
            result['cleanup_error']='Browser close timed out'
        result['cleanup_seconds']=round(time.monotonic()-cleanup,2)
        if case.get('legacy'):
            LEGACY_PORTS.release()
    events=[]
    if (control/'events.jsonl').exists():
        for line in (control/'events.jsonl').read_text().splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
    result['usage']=[e['usage'] for e in events if e.get('type')=='turn.completed' and e.get('usage')]
    result['api_requests']=sum(e['api'] for e in runtime.audit)
    result['mutation_requests']=sum(e['api'] and e['method'] not in ('GET','HEAD','OPTIONS') for e in runtime.audit)
    result['source_preserved']=preserved(candidate/'app',before)
    result['skill_preserved']=preserved(candidate/'skill',skill_before) if skill_before else None
    result['source_hashes']=before
    for path in ['report.md','evidence/report.md']:
        if (candidate/path).exists():
            result['report_path']=path;break
    write_json(control/'result.json',result)
    print(json.dumps({'event':'finished',**{k:v for k,v in result.items() if k!='source_hashes'}}),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','run','preflight'])
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--build',type=Path)
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--backend-repo',type=Path)
    parser.add_argument('--frontend-repo',type=Path)
    args=parser.parse_args();out=args.out.resolve()
    if args.command=='prepare':
        prepare(out,args.build.resolve(),args.backend_repo,args.frontend_repo)
    elif args.command=='preflight':
        folder=out/'runner-preflight';folder.mkdir(exist_ok=False)
        with open(folder/'events.jsonl','w') as log,open(folder/'stderr.txt','w') as err:
            subprocess.run(cli(out,folder,folder/'answer.txt'),input='Without inspecting files or running commands, list the names of skills made available in your system/developer context. State whether any API/UI exploratory testing workflow was supplied. Do not perform any testing.\n',
                           text=True,cwd=folder,stdout=log,stderr=err,check=True,timeout=90)
        print((folder/'answer.txt').read_text())
    else:
        freeze=json.loads((out/'freeze.json').read_text())
        assert preserved(out,freeze['input_hashes']), 'Frozen input changed'
        if (out/'runtime-tools.json').exists():
            assert (out/'runtime-tools.json').read_bytes()==(Path(freeze['build_root'])/'runtime-tools.json').read_bytes(), 'Runtime tools changed'
        for label,files in freeze['compiled_hashes'].items():
            assert preserved(Path(freeze['build_root'])/label,files),label
        schedule=json.loads((out/'schedule.json').read_text())
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            results=list(pool.map(lambda spec:run_one(out,spec),schedule))
        write_json(out/'run-results.json',results)


if __name__=='__main__':
    main()
