"""Separate Claude Code replication of frozen historical tasks; evaluator only."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
import study
from runtime import Runtime

HERE=Path(__file__).resolve().parent


def environment():
    env=dict(os.environ)
    for key in list(env):
        if key.startswith(('CLAUDE_','ANTHROPIC_')) and key!='ANTHROPIC_API_KEY':
            env.pop(key)
    if not env.get('ANTHROPIC_API_KEY'):
        raise RuntimeError('ANTHROPIC_API_KEY is not available; do not write it to study files')
    env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
    return env


def command(config, tools=True):
    return [shutil.which('claude'),'--bare','--disable-slash-commands','--setting-sources','',
            '--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence',
            '--no-chrome','--effort',config['effort'],'--model',config['model'],
            '--tools','Bash,Read,Write,Edit,Glob,Grep' if tools else '',
            '--permission-mode','bypassPermissions','--max-budget-usd',str(config['max_budget_usd_per_run']),
            '--append-system-prompt','A shared browser tool helper is available at tool-help/SKILL.md. Consult it when using Playwright CLI.',
            '-p','--output-format','stream-json','--verbose']


def prepare(source,out,model,budget,helper):
    if budget<=0:raise ValueError('Budget must be positive')
    parent=json.loads((source/'freeze.json').read_text())
    if any(not files for files in parent['compiled_hashes'].values()):
        raise ValueError('Parent study has missing compiled artifacts; rebuild and prepare it again')
    build=Path(parent['build_root'])
    for label,files in parent['compiled_hashes'].items():
        if not study.preserved(build/label,files):
            raise ValueError('Compiled artifacts changed or disappeared: '+label)
    out.mkdir(parents=True,exist_ok=False)
    for folder in ['sources','skills']:
        shutil.copytree(source/folder,out/folder)
    for file in ['sources.json','cases.json','schedule.json','protocol.md','template.md','skill-overrides.txt']:
        shutil.copy2(source/file,out/file)
    shutil.copy2(source/'freeze.json',out/'parent-freeze.json')
    for file in ['study.py','runtime.py','review.py','aggregate.py','claude_study.py']:
        shutil.copy2(HERE/file,out/file)
    shutil.copytree(helper,out/'tool-help',ignore=shutil.ignore_patterns('__pycache__','agents'))
    config={'model':model,'effort':'high','max_budget_usd_per_run':budget,
            'cli':subprocess.check_output([shutil.which('claude'),'--version'],text=True).strip(),
            'source_study':str(source),'session_prefix':'history-'+model.replace('claude-','')+'-'}
    study.write_json(out/'claude-config.json',config)
    (out/'claude-addendum.md').write_text('''# Claude replication addendum

This is a separate client/model study using the unchanged source, skill, cases, short task prompts,
report template, schedule and outcome criteria from the parent historical study. Skills were not
retuned using its outcomes. Every arm uses Claude Code with the pinned model and high effort.
The client receives Bash, Read, Write, Edit, Glob and Grep. Skills, plugins, project configuration,
MCP, personal instructions and persistence are disabled per process. A copied Playwright CLI
helper is available equally to all three arms; explicit invocation of the testing skill is evaluated.
There is no model fallback. The same 480-second deadline and instructed request/action budgets apply.
A per-run API spending guard is fixed in claude-config.json; budget-exhausted attempts remain results.

The reusable gateway's HEAD forwarding/audit repair and browser-close status retention are active.
These differ from the earlier frozen GPT controller, so raw between-model request/timing comparisons
are qualified. Native builds and test data are the same. Each candidate receives fresh application
state. Run after other historical studies finish because the legacy cases require fixed ports.
Claude Code and Codex have different system prompts, tools and token accounting: compare the skill's
increment within each client/model; this is not a controlled model-only leaderboard. The fresh
artifact review uses the same GPT reviewer and criteria, with condition labels withheld; that is a
further evaluator limitation. Raw Claude events, returned model identity, cache usage, cost and
permission denials are retained. No API credential or complete environment dump is recorded.
''')
    study.write_json(out/'freeze.json',{'created_at':time.time(),'model':model,'effort':'high',
        'client':'Claude Code','claude':config['cli'],'build_root':parent['build_root'],
        'compiled_hashes':parent['compiled_hashes'],'parent_freeze_sha256':hashlib.sha256((source/'freeze.json').read_bytes()).hexdigest(),
        'input_hashes':study.hashes(out)})
    print(out,flush=True)


def read_events(file):
    events=[]
    if file.exists():
        for line in file.read_text().splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
    return events


def apply_usage(result,events):
    finals=[e for e in events if e.get('type')=='result']
    initial=[e for e in events if e.get('type')=='system' and e.get('subtype')=='init']
    result['client_init']=[{k:e.get(k) for k in ['model','tools','mcp_servers','plugins','skills','slash_commands','apiKeySource']} for e in initial]
    result['cost_usd']=None
    result['usage']=[]
    if finals:
        final=finals[-1];raw=final.get('usage') or {}
        result['usage_raw']=raw;result['model_usage']=final.get('modelUsage')
        result['cost_usd']=final.get('total_cost_usd')
        result['client_result_subtype']=final.get('subtype')
        result['permission_denials']=final.get('permission_denials',[])
        if raw:
            result['usage']=[{'input_tokens':sum(raw.get(k,0) for k in ['input_tokens','cache_read_input_tokens','cache_creation_input_tokens']),
                              'cached_input_tokens':raw.get('cache_read_input_tokens',0),
                              'cache_write_input_tokens':raw.get('cache_creation_input_tokens',0),
                              'output_tokens':raw.get('output_tokens',0)}]
        if result['status']=='completed' and final.get('is_error'):
            result['status']='budget-exhausted' if 'budget' in str(final.get('subtype')) else 'runner-error'
    elif result['status']=='completed':
        result['status']='missing-client-result'


def run_one(out,spec):
    config=json.loads((out/'claude-config.json').read_text())
    case=next(c for c in json.loads((out/'cases.json').read_text()) if c['id']==spec['case_id'])
    build=Path(json.loads((out/'freeze.json').read_text())['build_root'])
    folder=out/spec['id'];folder.mkdir(exist_ok=False)
    candidate,control=folder/'candidate',folder/'controller'
    candidate.mkdir();control.mkdir();(candidate/'evidence').mkdir()
    for destination,source in case.get('sources',{}).items():
        shutil.copytree(out/'sources'/source,candidate/'app'/destination)
    shutil.copytree(out/'tool-help',candidate/'tool-help')
    if spec['condition']=='skill':shutil.copytree(out/'skills'/f"{case['surface']}-exploratory-testing",candidate/'skill')
    elif spec['condition']=='template':shutil.copy2(out/'template.md',candidate/'REPORT-TEMPLATE.md')
    before=study.hashes(candidate/'app');skill_before=study.hashes(candidate/'skill') if (candidate/'skill').exists() else None
    session=config['session_prefix']+spec['id']
    result={**spec,'model':config['model'],'status':'infrastructure-error','exit_code':None,'elapsed_seconds':0,
            'usage':[],'report_path':None,'api_requests':0,'mutation_requests':0,'source_preserved':True,'skill_preserved':None}
    runtime=Runtime(build,control,backend=case['backend'],frontend=case.get('frontend'),outage=case.get('outage',False))
    setup=time.monotonic()
    print(json.dumps({'event':'starting',**spec}),flush=True)
    if case.get('legacy'):study.LEGACY_PORTS.acquire()
    try:
        runtime.start();result['startup_seconds']=round(time.monotonic()-setup,2)
        task=study.task_text(case,runtime.url,session,spec['condition'])
        (candidate/'TASK.md').write_text(task)
        result['task_sha256']=hashlib.sha256(task.encode()).hexdigest();result['url']=runtime.url
        cmd=command(config);study.write_json(control/'command.json',cmd)
        started=time.monotonic()
        with (control/'events.jsonl').open('w') as log,(control/'stderr.txt').open('w') as err:
            proc=subprocess.Popen(cmd,cwd=candidate,env=environment(),stdin=subprocess.PIPE,stdout=log,stderr=err,start_new_session=True)
            try:
                proc.communicate(input=b'Read TASK.md and perform the assessment.\n',timeout=480)
                result['exit_code']=proc.returncode;result['status']='completed' if proc.returncode==0 else 'runner-error'
            except subprocess.TimeoutExpired:
                result['status']='timeout';os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                result['exit_code']=proc.returncode
        result['elapsed_seconds']=round(time.monotonic()-started,2)
    except Exception as exc:result['error']=type(exc).__name__+': '+str(exc)
    finally:
        cleanup=time.monotonic();runtime.stop()
        try:
            close=subprocess.run(['playwright-cli','-s='+session,'close'],cwd=candidate,capture_output=True,text=True,timeout=20)
            result['browser_close_exit_code']=close.returncode
            (control/'browser-close.txt').write_text(close.stdout+close.stderr)
        except subprocess.TimeoutExpired:result['cleanup_error']='Browser close timed out'
        result['cleanup_seconds']=round(time.monotonic()-cleanup,2)
        if case.get('legacy'):study.LEGACY_PORTS.release()
    events=read_events(control/'events.jsonl');apply_usage(result,events)
    final=next((e for e in reversed(events) if e.get('type')=='result'),None)
    if final:(control/'final.txt').write_text(final.get('result',''))
    result['api_requests']=sum(e['api'] for e in runtime.audit)
    result['mutation_requests']=sum(e['api'] and e['method'] not in ('GET','HEAD','OPTIONS') for e in runtime.audit)
    result['source_preserved']=study.preserved(candidate/'app',before)
    result['skill_preserved']=study.preserved(candidate/'skill',skill_before) if skill_before else None
    result['source_hashes']=before
    for path in ['report.md','evidence/report.md']:
        if (candidate/path).exists():result['report_path']=path;break
    study.write_json(control/'result.json',result)
    print(json.dumps({'event':'finished',**{k:v for k,v in result.items() if k not in ['source_hashes','usage_raw','model_usage','client_init']}}),flush=True)


def verify(out):
    freeze=json.loads((out/'freeze.json').read_text())
    assert study.preserved(out,freeze['input_hashes']),'Frozen input changed'
    build=Path(freeze['build_root'])
    for label,files in freeze['compiled_hashes'].items():assert study.preserved(build/label,files),label


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','preflight','run'])
    p.add_argument('--source',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--model');p.add_argument('--max-budget-usd',type=float,default=1.5)
    p.add_argument('--helper',type=Path,default=Path.home()/'.codex/skills/playwright-cli');p.add_argument('--workers',type=int,default=3)
    a=p.parse_args();out=a.out.resolve()
    if a.command=='prepare':
        if not a.model or not a.source:p.error('prepare requires --source and --model')
        prepare(a.source.resolve(),out,a.model,a.max_budget_usd,a.helper.resolve())
    else:
        verify(out);environment()
        if a.command=='preflight':
            folder=out/'runner-preflight';folder.mkdir(exist_ok=False)
            shutil.copytree(out/'tool-help',folder/'tool-help')
            config=json.loads((out/'claude-config.json').read_text());config['max_budget_usd_per_run']=.5
            with (folder/'events.jsonl').open('w') as log,(folder/'stderr.txt').open('w') as err:
                result=subprocess.run(command(config),input='Without inspecting files or using tools, list the names of skills, plugins, MCP servers and project instructions supplied in your context. State whether an API/UI exploratory testing workflow was supplied. Do not perform testing.\n',text=True,cwd=folder,env=environment(),stdout=log,stderr=err,timeout=90)
            status={'exit_code':result.returncode,'status':'completed' if result.returncode==0 else 'runner-error'}
            apply_usage(status,read_events(folder/'events.jsonl'));study.write_json(folder/'result.json',status)
            print(json.dumps(status,indent=2))
        else:
            schedule=json.loads((out/'schedule.json').read_text())
            with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
                list(pool.map(lambda spec:run_one(out,spec),schedule))
