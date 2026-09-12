#!/usr/bin/env node
import * as fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';

const packageRoot = fileURLToPath(new URL('../', import.meta.url));
const agents = {
  claude: {project: '.claude/skills', global: '.claude/skills'},
  codex: {project: '.agents/skills', global: '.agents/skills'},
  cursor: {project: '.cursor/skills', global: '.cursor/skills'},
  copilot: {project: '.github/skills', global: '.copilot/skills'},
};
const skills = {api: 'api-exploratory-testing', ui: 'ui-exploratory-testing'};
const help = `Install exploratory testing skills (Node.js 20+).

Usage: exploratory-skills --agent <claude|codex|cursor|copilot> [options]

  --project <path>   Project directory (default: current directory)
  --global           Install for your user instead of one project
  --skill <api|ui|all>  Choose a skill (default: all); full skill names also work
  --dry-run          Show changes without writing files
  --force            Replace differing copies after backing them up
  --help             Show this help

Examples:
  exploratory-skills --agent claude
  exploratory-skills --agent codex --project /path/to/project --skill api
  exploratory-skills --agent cursor --global --dry-run
  exploratory-skills --agent copilot --force

Existing identical copies are left alone. Conflicts stop the entire plan before
writes unless --force is set. Backups stay under .exploratory-skills-backups/
in the chosen project or home directory, outside agent discovery directories.
`;

function parse(args) {
  const options = {skill: 'all'};
  for (let i = 0; i < args.length; i++) {
    const flag = args[i];
    if (['--help', '-h'].includes(flag)) return {help: true};
    if (['--global', '--dry-run', '--force'].includes(flag)) {
      options[flag.slice(2)] = true;
    } else if (['--agent', '--project', '--skill'].includes(flag)) {
      const value = args[++i];
      if (!value || value.startsWith('--')) throw new Error(`Missing value for ${flag}`);
      options[flag.slice(2)] = value;
    } else throw new Error(`Unknown argument: ${flag}. Use --help.`);
  }
  if (!Object.hasOwn(agents, options.agent ?? '')) throw new Error('Choose --agent claude, codex, cursor or copilot. Use --help.');
  if (options.global && options.project) throw new Error('Use either --global or --project, not both.');
  if (options.skill !== 'all' && !Object.hasOwn(skills, options.skill) && !Object.values(skills).includes(options.skill)) {
    throw new Error('Choose --skill api, ui or all (or a full skill name).');
  }
  return options;
}

async function stat(file) {
  try { return await fs.lstat(file); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

async function inventory(directory) {
  const result = new Map();
  async function walk(current, relative = '') {
    const info = await fs.lstat(current);
    if (info.isSymbolicLink()) throw new Error(`Refusing to follow symbolic link: ${current}`);
    if (info.isDirectory()) {
      if (relative) result.set(`${relative}/`, null);
      for (const name of (await fs.readdir(current)).sort()) await walk(path.join(current, name), path.join(relative, name));
    } else if (info.isFile()) result.set(relative, await fs.readFile(current));
    else throw new Error(`Unsupported file type: ${current}`);
  }
  await walk(directory);
  return result;
}

function identical(a, b) {
  return a.size === b.size && [...a].every(([key, value]) =>
    b.has(key) && (value === null ? b.get(key) === null : Buffer.isBuffer(b.get(key)) && value.equals(b.get(key))));
}

async function ensurePlainParents(base, relative) {
  let current = base;
  for (const segment of relative.split('/')) {
    current = path.join(current, segment);
    const info = await stat(current);
    if (info && (!info.isDirectory() || info.isSymbolicLink())) throw new Error(`Expected a regular directory, not a link or file: ${current}`);
  }
}

export async function install(args, {cwd = process.cwd(), home = os.homedir(), log = console.log} = {}) {
  const options = parse(args);
  if (options.help) { log(help); return []; }
  const base = await fs.realpath(options.global ? home : path.resolve(cwd, options.project ?? '.'));
  if (!(await fs.stat(base)).isDirectory()) throw new Error(`Not a directory: ${base}`);
  const relative = agents[options.agent][options.global ? 'global' : 'project'];
  await ensurePlainParents(base, relative);
  const destinationRoot = path.join(base, relative);
  const names = options.skill === 'all' ? Object.values(skills) : [skills[options.skill] ?? options.skill];
  const plan = [];
  for (const name of names) {
    const source = path.join(packageRoot, 'skills', name);
    const destination = path.join(destinationRoot, name);
    const sourceFiles = await inventory(source);
    if (!sourceFiles.has('SKILL.md')) throw new Error(`Package is missing ${name}/SKILL.md`);
    const existing = await stat(destination);
    if (existing && (!existing.isDirectory() || existing.isSymbolicLink())) throw new Error(`Skill destination is not a regular directory: ${destination}`);
    const action = !existing ? 'install' : identical(sourceFiles, await inventory(destination)) ? 'unchanged' : 'replace';
    plan.push({name, source, destination, action});
  }
  for (const item of plan) log(`${options['dry-run'] ? 'Plan' : 'Skill'}: ${item.action} ${item.destination}`);
  const conflicts = plan.filter(item => item.action === 'replace');
  if (conflicts.length && !options.force) throw new Error('Existing skill differs. No files changed. Review it, then use --force to replace with a backup.');
  if (options['dry-run']) return plan;
  const changes = plan.filter(item => item.action !== 'unchanged');
  if (!changes.length) return plan;

  await ensurePlainParents(base, '.exploratory-skills-backups');
  // Stage complete copies before touching any existing skill.
  const stage = await fs.mkdtemp(path.join(base, '.exploratory-skills-stage-'));
  const completed = [];
  let backupRoot;
  try {
    for (const item of changes) await fs.cp(item.source, path.join(stage, item.name), {recursive: true, errorOnExist: true, force: false});
    await fs.mkdir(destinationRoot, {recursive: true});
    if (conflicts.length) {
      const backups = path.join(base, '.exploratory-skills-backups');
      await fs.mkdir(backups, {recursive: true});
      backupRoot = await fs.mkdtemp(path.join(backups, `${options.agent}-${Date.now()}-`));
    }
    for (const item of changes) {
      const backup = item.action === 'replace' ? path.join(backupRoot, item.name) : null;
      // Avoid overwriting a target created between planning and installation.
      if (!backup && await stat(item.destination)) throw new Error(`Destination appeared during installation: ${item.destination}`);
      if (backup) await fs.rename(item.destination, backup);
      completed.push({...item, backup, installed: false});
      await fs.rename(path.join(stage, item.name), item.destination);
      completed.at(-1).installed = true;
      log(`Installed: ${item.destination}`);
      if (backup) log(`Backup: ${backup}`);
    }
  } catch (error) {
    for (const item of completed.reverse()) {
      if (item.installed) await fs.rm(item.destination, {recursive: true});
      if (item.backup) await fs.rename(item.backup, item.destination);
    }
    throw error;
  } finally {
    await fs.rm(stage, {recursive: true, force: true});
  }
  log('Open a new agent session if the skills are not listed yet. No browser runtime was installed.');
  return plan;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === await fs.realpath(process.argv[1]).catch(() => '')) {
  install(process.argv.slice(2)).catch(error => {
    console.error(`exploratory-skills: ${error.message}`);
    process.exitCode = 1;
  });
}
