import {test} from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {install} from '../bin/install.mjs';

const repo = fileURLToPath(new URL('../', import.meta.url));
const names = ['api-exploratory-testing', 'ui-exploratory-testing'];
const quiet = () => {};
async function fixture(t) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'exploratory-installer-'));
  t.after(() => fs.rm(root, {recursive: true, force: true}));
  const project = path.join(root, 'project with spaces');
  const home = path.join(root, 'isolated-home');
  await fs.mkdir(project); await fs.mkdir(home);
  return {root, project, home};
}

for (const [agent, projectPath, globalPath] of [
  ['claude', '.claude/skills', '.claude/skills'],
  ['codex', '.agents/skills', '.agents/skills'],
  ['cursor', '.cursor/skills', '.cursor/skills'],
  ['copilot', '.github/skills', '.copilot/skills'],
]) {
  test(`${agent}: project and user installs preserve both skills and references`, async t => {
    const {root, project, home} = await fixture(t);
    await install(['--agent', agent, '--project', project], {cwd: root, home, log: quiet});
    await install(['--agent', agent, '--global'], {cwd: project, home, log: quiet});
    for (const base of [path.join(project, projectPath), path.join(home, globalPath)]) {
      for (const name of names) {
        assert.deepEqual(await fs.readFile(path.join(base, name, 'SKILL.md')), await fs.readFile(path.join(repo, 'skills', name, 'SKILL.md')));
        assert.deepEqual(await fs.readFile(path.join(base, name, 'references/reporting.md')), await fs.readFile(path.join(repo, 'skills', name, 'references/reporting.md')));
        await assert.rejects(fs.lstat(path.join(base, name, 'agents')), {code: 'ENOENT'});
      }
    }
    const again = await install(['--agent', agent], {cwd: project, home, log: quiet});
    assert.ok(again.every(item => item.action === 'unchanged'));
  });
}

test('dry run and invalid options never create agent folders', async t => {
  const {project, home} = await fixture(t);
  const plan = await install(['--agent', 'codex', '--dry-run'], {cwd: project, home, log: quiet});
  assert.equal(plan.length, 2);
  for (const args of [['--agent', 'invalid'], ['--agent', 'claude', '--global', '--project', project], ['--agent', 'codex', '--skill', '../other']]) {
    await assert.rejects(install(args, {cwd: project, home, log: quiet}));
  }
  assert.deepEqual(await fs.readdir(project), []);
  assert.deepEqual(await fs.readdir(home), []);
});

test('one conflicting skill prevents all writes; force preserves original outside discovery', async t => {
  const {project, home} = await fixture(t);
  const api = path.join(project, '.claude/skills', names[0]);
  const ui = path.join(project, '.claude/skills', names[1]);
  await fs.mkdir(ui, {recursive: true});
  await fs.writeFile(path.join(ui, 'SKILL.md'), 'personal edits');
  await fs.writeFile(path.join(ui, 'custom.txt'), 'extra file');
  await assert.rejects(install(['--agent', 'claude'], {cwd: project, home, log: quiet}), /Existing skill differs/);
  await assert.rejects(fs.lstat(api), {code: 'ENOENT'});
  const lines = [];
  await install(['--agent', 'claude', '--force'], {cwd: project, home, log: line => lines.push(line)});
  const backup = lines.find(line => line.startsWith('Backup: ')).slice(8);
  assert.equal(await fs.readFile(path.join(backup, 'SKILL.md'), 'utf8'), 'personal edits');
  assert.equal(await fs.readFile(path.join(backup, 'custom.txt'), 'utf8'), 'extra file');
  assert.ok(backup.startsWith(path.join(await fs.realpath(project), '.exploratory-skills-backups')));
  await assert.rejects(fs.lstat(path.join(ui, 'custom.txt')), {code: 'ENOENT'});
});

test('individual skill and full skill name select only the requested skill', async t => {
  const {project, home} = await fixture(t);
  const result = await install(['--agent', 'cursor', '--skill', 'ui-exploratory-testing'], {cwd: project, home, log: quiet});
  assert.equal(result.length, 1);
  assert.deepEqual(await fs.readdir(path.join(project, '.cursor/skills')), [names[1]]);
});

test('refuses linked destination parents and linked existing skill content', async t => {
  const {root, project, home} = await fixture(t);
  const outside = path.join(root, 'outside'); await fs.mkdir(outside);
  await fs.symlink(outside, path.join(project, '.claude'), 'dir');
  await assert.rejects(install(['--agent', 'claude', '--force'], {cwd: project, home, log: quiet}), /not a link/);
  assert.deepEqual(await fs.readdir(outside), []);
  const api = path.join(project, '.cursor/skills', names[0]); await fs.mkdir(api, {recursive: true});
  await fs.writeFile(path.join(outside, 'file'), 'original');
  await fs.symlink(path.join(outside, 'file'), path.join(api, 'SKILL.md'));
  await assert.rejects(install(['--agent', 'cursor', '--force'], {cwd: project, home, log: quiet}), /symbolic link/);
  assert.equal(await fs.readFile(path.join(outside, 'file'), 'utf8'), 'original');
});

test('rolls back completed replacements when installation is interrupted by an error', async t => {
  const {project, home} = await fixture(t);
  const api = path.join(project, '.claude/skills', names[0]);
  await fs.mkdir(api, {recursive: true});
  await fs.writeFile(path.join(api, 'SKILL.md'), 'original');
  await assert.rejects(install(['--agent', 'claude', '--force'], {cwd: project, home, log: line => {
    if (line.startsWith('Installed:')) throw new Error('Simulated interruption');
  }}), /Simulated interruption/);
  assert.equal(await fs.readFile(path.join(api, 'SKILL.md'), 'utf8'), 'original');
  await assert.rejects(fs.lstat(path.join(project, '.claude/skills', names[1])), {code: 'ENOENT'});
  assert.ok(!(await fs.readdir(project)).some(name => name.startsWith('.exploratory-skills-stage-')));
});

test('npm-style bin symlink executes the CLI rather than silently doing nothing', async t => {
  const {root, project} = await fixture(t);
  const bin = path.join(root, 'exploratory-skills');
  await fs.symlink(path.join(repo, 'bin/install.mjs'), bin);
  const result = spawnSync(process.execPath, [bin, '--agent', 'codex', '--dry-run'], {cwd: project, encoding: 'utf8'});
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Plan: install/);
  assert.deepEqual(await fs.readdir(project), []);
});
