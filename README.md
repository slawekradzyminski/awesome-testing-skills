# Exploratory Testing Skills

Two reusable agent skills for code-informed exploratory testing, adapted from Sławomir Radzymiński's September 2026 Playwright workshops.

| Skill | Purpose | Preferred runtime tool |
| --- | --- | --- |
| [api-exploratory-testing](skills/api-exploratory-testing/SKILL.md) | Inspect backend code, identify risks, probe the API, and report bugs and contract gaps | curl or another available HTTP client |
| [ui-exploratory-testing](skills/ui-exploratory-testing/SKILL.md) | Inspect application code, identify risky journeys, explore the interface, and report functional and nonfunctional findings | Playwright CLI or another available browser agent |

Both skills encourage users to supply the code being tested, then use that code to choose meaningful runtime experiments. They also work without source access and clearly distinguish a source-only assessment from live testing.

The experiment guides add practical techniques for selecting useful probes: challenge the first hypothesis, compare related results against business rules, investigate state transitions, distinguish uncertain writes from failed writes, and preserve the original failure while minimizing a reproduction. UI guidance also separates ordinary user interactions from diagnostic interventions that bypass normal controls.

Detailed guidance loads through references at the point of use. Each skill remains independently copyable, supports available tools, and avoids fixed test counts, mandatory full matrices, and extra approval steps for routine authorized work.

## Install

Requires **Node.js 20+**, npm/npx and Git. From the project where you want to use the skills:

```sh
npx --yes --allow-git=root --package='git+ssh://git@github.com/slawekradzyminski/exploratory-testing-skills.git#main' exploratory-skills --agent claude
```

Replace `claude` with **`codex`**, **`cursor`** or **`copilot`**. Both skills and their references are installed in the current project. The repository is currently private: the command requires GitHub access and working SSH authentication. It runs the package directly from Git; no npm-registry release or npm account is required. See [npm's execution documentation](https://docs.npmjs.com/cli/npm-exec/).

The command opts into fetching this direct Git package with `--allow-git=root`; npm 12 blocks Git packages by default. This setting applies only to this invocation. Older npm versions that do not recognize the flag can omit it. See [npm's Git-fetch configuration](https://docs.npmjs.com/cli/install/#allow-git).

Add options to that command as needed:

| Option | Effect |
| --- | --- |
| `--agent claude` / `codex` / `cursor` / `copilot` | Select the client |
| `--project /path/to/project` | Install into another existing project; quote paths containing spaces |
| `--global` | Install in your home directory for use across projects |
| `--skill api` / `ui` / `all` | Choose one skill or both; default is `all` |
| `--dry-run` | Print the plan without changing files |
| `--force` | Replace differing copies after preserving backups |
| `--help` | Show usage and examples |

Identical copies are skipped. If either selected skill differs, installation stops before writes unless `--force` is supplied. Replacements preserve the complete previous directory under `.exploratory-skills-backups/` in the selected project or home directory; the command prints its path. Backups sit outside skill-discovery directories. To update, run the command again with `--force`; replace `#main` with a reviewed commit SHA when you need a fixed version. Keep personal edits in the backup or merge them deliberately.

If you prefer an authenticated clone, the same installer works locally without npm installation:

```sh
gh repo clone slawekradzyminski/exploratory-testing-skills
cd exploratory-testing-skills
node bin/install.mjs --agent codex --project /path/to/your/project
```

### Install locations and compatibility

The package uses the portable `SKILL.md` format with `references/`. It does not require a per-skill `agents/` directory, custom agent definitions, plugins or generated rules files.

| Client | Project directory | User directory | Documentation |
| --- | --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | [Claude skills](https://code.claude.com/docs/en/skills) |
| Codex | `.agents/skills/` | `~/.agents/skills/` | [Codex skills](https://learn.chatgpt.com/docs/build-skills) |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` | [Cursor skills](https://cursor.com/docs/skills) |
| GitHub Copilot | `.github/skills/` | `~/.copilot/skills/` | [Copilot skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) |

Paths were checked against official documentation on September 12, 2026. Codex's `.agents/skills/` discovery directory is different from optional `agents/openai.yaml` metadata inside a skill. Cursor and Copilot also recognize some shared/compatible directories, so a copy installed for one client can be visible in another; avoid duplicate copies in multiple directories the same client scans. Global installation applies locally; remote/cloud sessions need skills available in their own environment.

Open a new agent session if the skills are not listed yet. Ask the agent to use the skill by name; Codex supports `$api-exploratory-testing`, and Claude Code/Cursor expose skill names through their slash-command selectors. Skill discovery and available tools depend on the client/version. Installation paths and file integrity were tested; the behavioral evaluations below were run in Codex, not independently repeated in all four products.

The installer has no runtime dependencies or lifecycle install scripts. Its distributable contains the installer and skill files; benchmark fixtures and archived reports stay in the Git repository. No browser runtime, HTTP tool, account or credentials are configured for you. The UI skill prefers Playwright CLI when available and permits another browser agent.

For manual installation, copy a complete directory from `skills/` into the appropriate location above. To uninstall, remove only that installed skill directory after reviewing any personal changes; backups remain available separately.

## Example requests

```text
Use the api-exploratory-testing skill to explore the cart API.
Backend code: /path/to/backend, branch feature/cart-updates.
Test URL: http://localhost:8080.
Requirements: docs/cart-rules.md.
Use the two disposable customer accounts from the local test configuration.
You may create and delete your own test carts. Spend up to 20 minutes.
Identify risky areas and report reproducible bugs with HTTP evidence.
```

```text
Use the ui-exploratory-testing skill to explore account settings and profile editing.
Frontend: /path/to/frontend. Backend: /path/to/backend.
Test URL: http://localhost:3000. Start with the current local branches.
Use Playwright CLI, or the available browser agent if CLI is unavailable.
Use disposable test users; avoid sending real emails.
Inspect code first, prioritize risky states, and verify them in the browser.
Report findings, supporting evidence, and meaningful coverage gaps.
```

## Expected results

- A compact risk assessment grounded in source, requirements, and observations.
- Focused live experiments and reproducible, sanitized evidence.
- Findings that distinguish observed failures, code evidence, hypotheses, and ambiguous requirements.
- Explicit limits: build mismatch, missing source/runtime, untested states, and cleanup still needed.
- Suggested regression coverage at a suitable test level.

Exploration does not automatically include product fixes, a new regression suite, external issue filing, or publication. Those actions can be included in the user's task explicitly. Routine authorized testing continues without repeated approval requests.

## Workshop lineage

Reviewed against the latest remote branch tips on September 12, 2026:

- [`hyr21` at `94dccc853d421746956ea2691ed5c4fcaa81bf95`](https://github.com/slawekradzyminski/playwright-2026/tree/94dccc853d421746956ea2691ed5c4fcaa81bf95/.codex/skills): API/UI exploration, evidence, impact assessment, visual and network review.
- [`obi25` at `db0d9393bd11816f59c44f153c56b5474a71acdf`](https://github.com/slawekradzyminski/playwright-2026/tree/db0d9393bd11816f59c44f153c56b5474a71acdf/.claude/skills): backend assessment, actual test-assertion inspection, and test-level selection.

These are generic derivatives. They remove workshop-specific hosts, credentials, directory conventions, fixed viewport policies, automation rules, and duplicate Codex/Claude copies. They retain adaptive exploration and evidence standards, add explicit source intake and risk maps, and support alternative tools and partial access.

See [validation notes](docs/validation.md) for checks and their limits.

## Skill evaluations

The suite contains **14 runnable cases** with known defects, matching corrected controls, and useful non-bug outcomes. The aim is to assess exploration and reporting, including the ability to say that sampled checks passed, the environment was unavailable, or source access limited the assessment.

**Documentation-only defects are outside the benchmark.** New runs do not audit README text or OpenAPI documentation. They use requirements as context and assess application behavior, including misleading runtime validation feedback and rejection of valid input. Course documentation can be corrected independently of these frozen cases. The skills remain usable for broader exploration when requested.

| Group | Cases | What it assesses |
| --- | --- | --- |
| Cart API/UI with source | api-01, api-02, ui-01, ui-02 | Persisted negative quantity, Cancel submitting an edit, and matching clean controls |
| Deliberately limited access | api-03, ui-03 | Source-only reasoning and runtime-only bug investigation without invented access |
| Runtime works, source unavailable | api-04, ui-04 | Productive API/browser testing, passing evidence, and a useful source handoff |
| Unavailable environment | api-05, ui-05 | Bounded availability probes, honest blocked status, and actionable follow-up |
| Course-derived validation | api-06 through api-09 | Misleading length feedback and password character/byte mismatch, each with a corrected control |

The sample apps remain in this repo. Optional local/hosted Awesome LocalStack profiles provide public read-only exploration of a real deployment, with committed backend/frontend/stack sources when supplied. Their findings have no complete bug oracle and are kept separate from seeded-case recall. [Workshop provenance](evals/workshop-benchmarks.md) identifies the course reports used and future candidates such as QR decoding and unresolved policy questions.

### What we observed

| Evidence | Result | Interpretation |
| --- | --- | --- |
| [16-run paired pilot](evals/results/2026-09-12-retry.md) | Primary source-backed artifact scores: **11.75/12 with skills, 10.0/12 without**; both groups found both seeded defects | Stronger evidence in this small sample; no established discovery-rate advantage |
| [Ten practical trials](evals/results/2026-09-12-usability.md) | Six of eight initial cases met the desired useful outcome; two weaknesses were corrected and passed targeted reruns | Tests exposed excessive outage probing and an incomplete missing-source handoff; unsuccessful runs remain archived |
| Course defect/control pairs | Both defect cases identified; corrected controls produced evidence-backed passing reports | Finding a bug is not the only successful outcome |
| Historical hosted API comparison | Both conditions reproduced the same documentation mismatch, course DOC-08 | Preserved historical evidence; excluded from the current benchmark scope and discovery claims |

The unavailable-API correction reduced observed requests from **35 to 2** in its targeted rerun. The source-handoff correction made the report explain which frontend/backend code and deployed revision could improve a later assessment. Neither one-off rerun establishes a reliability rate.

### How grading works

A fresh agent receives a neutral task, its prepared source/runtime access and the reporting contract. Expected findings and controller logs stay outside its context. The agent submits a report, evidence, and individual `passed`, `failed`, `blocked` or `not-run` checks. A blocked functional assessment can still be a successful handling of an intentionally unavailable environment.

`harness.py grade` checks artifact structure, evidence paths, source preservation and corroborated HTTP facts. It does **not** automatically certify testing quality. The [review rubric](evals/rubric.md) assesses context, risk selection, experimental reasoning, evidence, finding accuracy and closeout. The pilot's twelve sample reports also received an independent review blind to the with/without condition; the practical correction pass was owner-reviewed. New unseeded functional findings are adjudicated on evidence rather than automatically rejected. Documentation-only observations receive no discovery credit; reviewers classify scope separately from false positives. Historical scores and raw evidence remain unchanged.

### Run an evaluation

From a clone of this repository, using Python 3.10+ and an available browser tool for UI cases:

```sh
python3 evals/harness.py prepare api-01 --out /tmp/exploration-eval-001
```

Give a **fresh agent context** only the printed `candidate/TASK.md` and its allowed resources. Preparation starts a fixture; it does not launch an agent. After the agent produces its report and submission:

```sh
python3 evals/harness.py grade /tmp/exploration-eval-001
python3 evals/harness.py stop /tmp/exploration-eval-001
```

Use a new output directory for every run; always stop the owned fixture after completion or failure. Add `--without-skill` at preparation for a baseline arm. [Full instructions](evals/README.md) cover source snapshots, live profiles, browser fixture validation and manual review.

Infrastructure checks are separate from agent scores:

```sh
npm test
python3 -m unittest discover -s evals/tests -v
python3 -m unittest discover -s evals/sample-app -v
```

`npm test` tests the installer. The Python checks test fixtures and grading safeguards. Passing them does not establish that an agent finds bugs.

### Limits

These are development cases, with one initial trial per condition/case, a small set of defect mechanisms, and guidance that already contains some relevant examples. They are not a held-out benchmark. Tool choices varied; exact model versions, full action traces, token costs and automatically enforced wall-clock budgets were unavailable. Fresh contexts are not OS sandboxes. We have not demonstrated equal behavioral performance across Claude Code, Codex, Cursor and Copilot.

The evidence supports an initial practical release with explicit limitations. Repeated held-out source-backed runs, fixed model/tool versions and natural skill-triggering tests are needed before making general performance claims. [Validation notes](docs/validation.md) and the archived assessments retain what was actually checked, including earlier failures. Removing optional display metadata does not retroactively change those evaluated snapshots or their hashes.
