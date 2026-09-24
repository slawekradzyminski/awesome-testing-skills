# Historical project comparison

This comparison uses real historical application revisions instead of seeded source mutations. It tests what an exploratory-testing skill adds to an ordinary request and to a compact reporting template. The [protocol](protocol.md), [case manifest](cases.json) and [source revisions](sources.json) are evaluator material: keep them away from candidate sessions.

The current study schedules 36 fresh sessions: four historical failures, one corrected control and one unavailable API, each in three conditions and two repetitions. Its results must remain separate from the earlier [Dispatch Desk study](../results/2026-09-12-journey-study.md). Infrastructure preflight is complete. The September 12 execution was [closed incomplete and ungraded](../results/2026-09-12-history-study.md): 24 completed sessions, four timeouts and eight interrupted/unstarted schedule entries. A separate September 24 [Opus 5.5 six-run cart diagnostic](../results/2026-09-24-history-opus55-diagnostic.md) covers one ticket only. The commands below describe the reusable full workflow, not work still running; the full Claude candidate matrix has not been launched.

## What “without skill” means

The normal condition gets a short feature request, original project source/docs, the running instance and operational information: allowed fixture changes, credentials, scope, tools, budget and output location. It gets no reporting template, risk checklist, prescribed experiments or evaluator-written business requirements. For example, the registration task starts:

```text
Test account registration and sign-in, and give the team your assessment.
Project source and its original documentation are in app/.
Test instance: <assigned loopback URL>
```

The [prompt constructor](study.py) shows every shared instruction. The template condition adds only the [report template](template.md). The skill condition adds the complete frozen API or UI skill, including its reporting guide. All conditions still have ordinary coding-agent instructions and the same Playwright CLI tool helper; this is not a comparison with an instruction-free model. Original documentation and tests can themselves guide testing. They are not rewritten to point toward the hidden faults.

## Historical cases

| Case | Source/runtime | Evaluator purpose |
| --- | --- | --- |
| task-01 | Original Java registration API | Duplicate email reaches an unhandled database constraint and returns 500 |
| task-02 | Original React cart, compatible native Spring backend | Populated cart is falsely presented as empty while details load |
| task-03 | Original React product details, compatible native backend | Valid long content overflows a narrow viewport |
| task-04 | Original React cart and compatible historical native backend | Refetched quantity/totals disagree with the retained editor after another client edit |
| task-05 | Fixed task-03 frontend | Evidence-backed passing assessment and restraint; other real defects remain admissible |
| task-06 | Corrected registration source, unavailable gateway | Honest blocked-runtime report, useful source analysis and proportionate stopping |

A fresh curator selected the historical mechanisms without inspecting the skill files or previous scores. The coordinating author knows the cases and verifies infrastructure. This is separation from skill authoring, not independent human research. Public historical code may have appeared in model training. The cases come from two related repositories, not a representative sample of production projects.

Each admitted defect/fix pair has two native runtime reproductions. A proposed authentication-filter case was excluded because only server logs differed: both revisions returned the same HTTP response. For cart synchronization, focus-only attempts failed; the retained reproduction uses a real second-tab edit and browser offline/online reconnection. These unsuccessful preflight attempts are part of the evidence, not candidate model failures.

## Build the actual revisions

Requirements: Python 3.12+, Git, Node 24, npm, JDK 21 for historical backends, JDK 25 for the compatible current backend, and Playwright CLI with a browser. Model runs require an authenticated Codex CLI with `gpt-6-astra` available. Builds download dependencies; candidate and reviewer runs consume model usage. Do not run this casually as a lightweight unit test.

Clone the [backend](https://github.com/slawekradzyminski/test-secure-backend) and [frontend](https://github.com/slawekradzyminski/vite-react-frontend) with their history available. Use fresh directories for every build and run. From this repository:

```sh
python3 evals/history-study/build.py \
  --backend-repo /path/to/test-secure-backend \
  --frontend-repo /path/to/vite-react-frontend \
  --java21 /path/to/jdk21/home \
  --java25 /path/to/jdk25/home \
  --out /tmp/history-build
```

The builder exports exact revisions with `git archive`, installs each original npm lockfile, and builds unchanged application source. Java builds skip test execution; building a jar is not proof that its test suite passes. Logs and resolved revisions are retained. The source repositories are not edited, reset or switched. Use historically compatible runtimes instead of silently upgrading old libraries.

The gateway serves the actual compiled React bundles and forwards real Java responses. Each process uses a new in-memory database. Test data are created through native APIs. Modern UI cases use the pinned compatible backend revision rather than pretending all frontend/backend snapshots were deployed together historically. Production images, optional external services and their integration correctness are excluded.

## Verify infrastructure before model runs

```sh
python3 -m unittest discover -s evals/history-study -p 'test_*.py' -v
python3 evals/history-study/check_api.py \
  --build /tmp/history-build --out /tmp/history-api-checks
python3 evals/history-study/check_ui.py \
  --build /tmp/history-build --out /tmp/history-ui-checks
python3 evals/history-study/check_legacy_ui.py \
  --build /tmp/history-build --out /tmp/history-legacy-checks
```

The scripts deliberately know the failures and fixes; they are infrastructure checks, not skill scores. They use real browser interactions and save screenshots and gateway audit evidence. The API command checks successful registration/sign-in, duplicate-email failure and a duplicate-username contrast. Independent API before/fix checks and rejected-case evidence are also retained with the curation record. Review opened screenshots and wire results before admitting a new case.

The legacy cart hardcodes `localhost:4001` for API calls and uses UI port 8081. The study serves the UI at `127.0.0.1:8081` to select its IPv4 gateway explicitly; some hosts answer `localhost:8081` from an unrelated IPv6 service. Both IPv4 ports must be free. Its runs acquire an exclusive lock; the controller never stops an unrelated service occupying either port. Other cases use assigned ephemeral loopback ports. Do not run multiple copies of the study or a legacy preflight simultaneously.

## Freeze, run and review

```sh
python3 evals/history-study/study.py prepare \
  --backend-repo /path/to/test-secure-backend \
  --frontend-repo /path/to/vite-react-frontend \
  --build /tmp/history-build --out /tmp/history-study
python3 /tmp/history-study/study.py preflight --out /tmp/history-study
```

Inspect the preflight answer: only the shared `playwright-cli` helper should be available, without either testing workflow. Preparation freezes source, skill, prompt/controller, protocol, schedule and compiled artifact hashes. Global skills/configuration overrides apply only to these processes; no permanent user settings change. Explicit invocation is tested, not automatic skill discovery.

```sh
python3 /tmp/history-study/study.py run --out /tmp/history-study --workers 3
python3 /tmp/history-study/review.py prepare \
  --source /tmp/history-study --out /tmp/history-review
python3 /tmp/history-study/review.py run \
  --source /tmp/history-study --out /tmp/history-review
python3 /tmp/history-study/aggregate.py \
  --source /tmp/history-study --reviews /tmp/history-review \
  --out /tmp/history-results.json
```

The first run command launches 36 candidate sessions; review launches nine additional sessions. Each candidate has eight minutes including reporting, up to 180 API requests and 100 browser actions. Original-file preservation, request counts, elapsed time and available tokens are recorded. Browser-action counts require trace review. All attempted runs, including errors and timeouts, stay in the record. A missing or incomplete review causes aggregation to fail rather than invent a score.

Candidate reports go to `candidate/report.md`, with supporting files in `candidate/evidence/`. Review also accepts the historical nested report location if used, without awarding schema-compliance points. Reviewers receive outcome criteria, original context, decisive evidence and runtime audits with condition labels withheld. Wording may still reveal the condition: describe the review as partially masked. Keep raw judgments and explicit owner adjudications separately.

Candidate/controller separation is a context boundary, not an operating-system sandbox. The runner grants broad local shell access for browser compatibility; use a dedicated machine/VM for untrusted candidates. Inspect traces for access violations. Never give a candidate this README, fixing commits, case manifest, curation report, answer key or other runs.

## Interpreting the result

Report actionable historical findings, additional valid findings, unsupported claims, handoff completeness and resources separately. A corrected control and an outage have different desired outcomes and do not increase the historical-discovery denominator. A source-only suspicion is not a runtime-confirmed bug. A correctly blocked assessment is not a functional test pass.

The full skill must add supported usefulness over both alternatives to justify an effectiveness claim in these tasks. Small differences, equal outcomes and regressions remain valid results. Fewer requests alone do not prove efficiency, and concurrent shared-host execution limits timing comparisons. Do not extend or retune the study selectively until a desired result appears.

## Executed snapshot and later runner repairs

The September 12 run executes its frozen controller/runtime copies. After it started, an independent source audit found that HEAD requests received the gateway's default 501 and were omitted from its audit, and that nonzero browser-close exits were not retained. Those are fixture/accounting limitations, not application defects. Review must inspect traces for HEAD probes and verify owned cleanup separately. Request totals from that snapshot are gateway-recorded lower bounds where HEAD was used; API-target totals also include proxied Swagger/static requests. API/action budgets are instructed and checked afterward, while the time limit is enforced.

The reusable runner now forwards and audits HEAD, preserves its response semantics, and retains browser-close output/status. The outage HEAD regression check passes. It also accepts explicit JDK paths and repository locations for fresh builds on other machines. These repairs do not retroactively change any candidate run, archived snapshot or historical result. The frozen study's native legacy applications use JDK21, while candidate shells default to the host's JDK25; original tests may therefore require additional compatible tooling even though the supplied runtime is ready. Assess actual reports before interpreting that limitation.

## Repeat the comparison with Claude

The separate [Claude runner](claude_study.py) reuses a prepared historical study's exact source, skills, tasks and schedule. It runs Claude Code through the Anthropic API, with personal configuration, automatic skill discovery, plugins and MCP disabled. The browser helper is copied equally into every arm. It preserves the built-in Claude Code tools/system behavior, so evaluate the skill's improvement **within each client/model**; differences from Codex cannot be attributed to the model alone.

The API key must already be in `ANTHROPIC_API_KEY`. Never put its value in this repository, a command argument or a saved configuration. Query Anthropic's [Models API](https://platform.claude.com/docs/en/api/models/list) to choose an available exact model ID. September 12 setup verified `claude-sonnet-5`; availability and the model returned by each run are recorded separately. The installed CLI supports the [non-interactive options](https://code.claude.com/docs/en/headless) used here.

```sh
python3 evals/history-study/claude_study.py prepare \
  --source /tmp/history-study --out /tmp/history-sonnet \
  --model claude-sonnet-5 --max-budget-usd 1.50
python3 /tmp/history-sonnet/claude_study.py preflight --out /tmp/history-sonnet
```

Inspect the preflight initialization and answer before execution: no exploratory workflow, loaded plugins or MCP servers should be present. Then, after any other historical study has finished using the fixed legacy ports:

```sh
python3 /tmp/history-sonnet/claude_study.py run --out /tmp/history-sonnet --workers 3
python3 /tmp/history-sonnet/review.py prepare \
  --source /tmp/history-sonnet --out /tmp/history-sonnet-review
python3 /tmp/history-sonnet/review.py run \
  --source /tmp/history-sonnet --out /tmp/history-sonnet-review
python3 /tmp/history-sonnet/aggregate.py \
  --source /tmp/history-sonnet --reviews /tmp/history-sonnet-review \
  --out /tmp/history-sonnet-results.json
```

This schedules 36 paid candidate sessions plus nine Codex artifact reviews. The example's per-session API guard allocates $54 across candidates; setup checks are additional. A client spending guard is not a guarantee against a final in-flight request exceeding it. Budget exhaustion, timeouts, errors and missing usage remain visible, with no silent retries or model fallback. Keep each model's artifacts and summaries separate. Do not launch an Opus batch merely because the Sonnet result is disappointing; choose models and budgets before inspecting their candidate outcomes.

Claude input-token totals are normalized as fresh input plus cache reads plus cache creation; raw provider fields, model usage and CLI-reported estimated dollar cost remain in each result. The aggregation's existing token columns are not a price calculator. The repaired HEAD gateway and retained browser-close status apply to this new replication, while the earlier GPT snapshot retains its disclosed limitations. Neither case selection nor skills change between models.

## Retain the evidence

After candidate execution, complete review, corroboration and any explicit adjudication, use `archive.py --source /tmp/history-study --reviews /tmp/history-review --out /path/to/new-archive`. It retains prompts, frozen controllers, results, traces and evidence. Exact duplicate source/skill and reviewed files become relative symlinks **after** evaluation; candidate and reviewer sessions themselves used separate real copies. Original files and any normalized review differences retain their bytes. The artifact index records checksums and link targets. Inspect the result and add the assessment, independent preflight/corroboration and adjudication records before publishing it.
