# Exploratory skill evaluations

Start with the [user guide](GETTING_STARTED.md) for local fixtures, public targets, source links and a complete prepare → agent → grade → cleanup walkthrough.

The separate [Dispatch Desk screening study](journey-study/) compares a normal request, a reporting template and the full skill on broader journeys, with a frozen protocol and repeated fresh sessions. It has its own runner and evidence review; its cases and results are not merged with the 18-case suite below. The [completed 24-run assessment](results/2026-09-12-journey-study.md) found all three conditions established every seeded fault with actionable evidence; it does not demonstrate an effectiveness advantage for the full skill.

A separate [Claude Opus 5.5 four-arm development pilot](results/2026-09-24-claude-ablation.md) splits API investigation and reporting guidance and scores candidate-observed state from the runtime audit. All four arms again reached 3/3 on the known-ceiling Dispatch Desk API fixture, so it does not establish an advantage. The same result includes fresh API/UI behavior checks of the new check-ledger, screenshot, visit-log and HTTP-evidence guidance. The [pilot protocol and runner](journey-study/claude-ablation.md) remain separate from both the 18-case suite and the historical study.

A later [six-run Opus 5.5 historical cart diagnostic](results/2026-09-24-history-opus55-diagnostic.md) used two frozen repetitions of one real React/Java ticket across ordinary, template and full-skill conditions. All reported a related direct-update defect, but none reproduced the prespecified two-tab reconnect target. The full skill produced check ledgers in both runs; no run saved a correlated HTTP exchange log. This is not the full historical matrix or an effectiveness ranking.

This suite evaluates an agent using the API/UI skills. It keeps three kinds of evidence separate:

1. **Infrastructure checks:** does the fixture, mutation application, isolation, and artifact validator work?
2. **Seeded agent evaluations:** can a fresh agent identify a known defect, produce convincing evidence, prioritize risks, and avoid unsupported findings in matching controls?
3. **Real Awesome LocalStack evaluations:** does the skill support useful exploration on an actual deployment with unknown bugs and possible source/build drift?

The first category cannot substitute for the other two. `harness.py grade` performs deterministic integrity checks; an evidence-based review using [rubric.md](rubric.md) decides the testing-quality result.

**Current scope excludes documentation-only defects.** New tasks assess application behavior and useful reporting, not README/OpenAPI documentation accuracy. Requirements remain context; incorrect runtime validation feedback and rejection of valid input remain functional findings. The shared output contract applies this boundary to both comparison conditions, and new manifests record it. Human reviewers classify claims; the grader does not infer defect categories from keywords. Historical reports retain their original scope and evidence, including the hosted DOC-08 observation, which is excluded from current discovery claims.

The **primary comparison uses source plus runtime**. Supply the actual backend, frontend and stack sources for live runs. The explicitly source-only/runtime-only cases are supplementary robustness checks that deliberately restrict access; they are not evidence that available project source was missing. Report their results separately from the primary comparison.

## Kept sample repository

[sample-app](sample-app/) is a small self-contained application that stays in this repository. It requires Python 3.10+ and an available browser agent for UI work. It uses Awesome LocalStack's product/cart route conventions and quantity rules, but has its own implementation, disposable identities, and in-memory state. It is not a copy of Spring, React, SSO, or the production stack. See [requirements](sample-app/requirements.md).

The baseline application is the control. The evaluator-only harness applies one frozen change to an isolated copy: accepting a negative quantity, or allowing Cancel to submit an edit. The agent sees the resulting code when source is available, never a variant flag or the expected finding. The sample's existing tests intentionally cover only a narrow slice of behavior. [Input-validation case provenance](workshop-benchmarks.md) add a separate retained validation fixture and practical reporting cases; the suite now contains 18 cases, including the [orders/profile validation app](validation-app/).

## Run a case

From the repository root:

```sh
python3 -m unittest discover -s evals/tests -v
python3 -m unittest discover -s evals/sample-app -v
python3 evals/harness.py prepare api-01 --out /tmp/exploration-eval-001
```

Use a fresh, nonexistent output directory for every run. Preparation starts a loopback fixture for runtime cases and prints the candidate task path. Give a **fresh agent context** only that `candidate/TASK.md`, its candidate directory, and the assigned runtime. Do not preload the original repository, this README, prior reports, `cases.json`, the controller folder, or the hidden expected results. Give it its ordinary tools, including an HTTP client or browser agent. The candidate may inspect only its prepared directory and assigned runtime.

After the agent finishes:

```sh
python3 evals/harness.py grade /tmp/exploration-eval-001
python3 evals/harness.py stop /tmp/exploration-eval-001
```

Always stop owned fixtures, including after failed evaluations. Preparation and stopping do not start, reset, or stop Docker or external applications. Runs are isolated by directories, process, port, and disposable state. The candidate/controller separation is a **context boundary, not an operating-system security sandbox**; use a restricted container/VM for untrusted runners.

For a baseline comparison, prepare the same case with `--without-skill` and use another fresh agent context. Keep the model, budget, tool versions, and environment fixed. The baseline retains the same task and output contract. Repeated runs and counterbalanced order are needed before claiming an improvement due to the skill.

| Case | Surface | Group / access | Purpose (evaluator-only) |
| --- | --- | --- | --- |
| api-01 | API | Primary: source + runtime | Detect persisted negative quantity |
| api-02 | API | Primary: source + runtime | Matching control; evaluate restraint and risk assessment |
| ui-01 | UI | Primary: source + runtime | Detect Cancel sending an update and persisting it |
| ui-02 | UI | Primary: source + runtime | Matching control; inspect ordinary Save/Cancel behavior |
| api-03 | API | Supplementary: source only | Find code-level defect without claiming runtime execution |
| ui-03 | UI | Supplementary: runtime only | Explore without repeatedly blocking on missing source |
| api-04 / ui-04 | API / UI | Usability: runtime only | Clean control; test productively and explain what source could add |
| api-05 / ui-05 | API / UI | Usability: source + unavailable gateway | Recognize blocked functional testing and provide useful handoff |
| api-06 / api-07 | API | Input validation: source + runtime | Misleading maximum-length guidance and matching corrected control |
| api-08 / api-09 | API | Input validation: source + runtime | Password character/byte contract mismatch and matching corrected control |
| api-10 / api-11 | API | Orders/profile: source + runtime | Order ownership defect and corrected control |
| ui-06 / ui-07 | UI | Orders/profile: source + runtime | Profile Cancel submitting a save and corrected control |

Candidates receive neutral application tasks with a five-minute budget, up to 60 API requests or 45 browser actions. The fixture's server audit corroborates requests; a reviewer checks browser actions, opened screenshots, meaning of findings, and untested claims. Audit route paths omit query strings: the grader matches the parsed route and flags query-bearing observations for manual evidence review. It does not independently prove query/header/body-specific claims. The harness currently reports request counts but does not automatically measure browser-action counts or token usage. Record those from the runner transcript when available.

New runs use reporting version 2: individual checks have evidence and passed/failed/blocked/not-run outcomes. `runtime_exercised` distinguishes functional application testing from availability attempts. Unexpected environment failures are inconclusive for discovery trials; intentional unavailable cases assess the usefulness of the agent's blocked report. The [rubric](rubric.md) grades these outcomes explicitly.

To verify the browser fixture itself, with `playwright-cli` and a browser installed:

```sh
python3 evals/check_browser_fixture.py --out /tmp/browser-fixture-check-001
```

This script clicks Cancel and Save in fresh mutation/control instances, checks persisted state and HTTP writes, saves screenshots/command evidence, and closes its owned sessions and servers. It already knows the expected result, so its success is **infrastructure validation, not a skill score**.

## Orders/profile validation app

[validation-app](validation-app/) integrates the original [smoke-test demo](../docs/validation-fixture/server.py) as four reproducible cases. Its corrected base enforces order ownership and prevents Cancel submitting a profile edit. The harness applies one defect at a time to a fresh copy; source, lifecycle and HTTP audit records use the same contract as the other fixtures. The original demo and its historical evidence remain unchanged.

Run it directly with `python3 evals/validation-app/app.py --port 8090`, or use `prepare api-10` / `prepare ui-06` for isolated benchmark cases. Validate the browser pair with `python3 evals/check_browser_fixture.py --suite validation --out /tmp/profile-fixture-check-001`. These new cases have infrastructure checks, not fresh agent-effectiveness measurements.

## Actual Awesome LocalStack profiles

[profiles.json](profiles.json) supports local `http://localhost:8081`, stable hosted `https://awesome.byst.re`, and disposable hosted `https://aitesters.byst.re`, each with API/UI tasks. All provided live tasks are **public read-only**. Even the disposable sandbox is shared, so its existence is not permission to reset other users' state.

```sh
python3 evals/harness.py preflight localstack-hosted-api
python3 evals/harness.py prepare-live localstack-hosted-api \
  --out /tmp/localstack-eval-001 \
  --backend /path/to/test-secure-backend \
  --stack /path/to/awesome-localstack
```

For UI source context, add `--frontend /path/to/vite-react-frontend`. Source snapshots are taken from each checkout's committed HEAD; uncommitted changes and Git history are excluded. This preserves the original working trees and records revisions/hashes. Candidates receive the commit IDs in `source-revisions.json`, so they do not need Git history to identify supplied source. Source snapshots may still contain private project information; runs remain local until reviewed for publication. They are not evidence that the deployment uses those commits. With no supplied source, the task explicitly uses runtime-only exploration; use that mode only for a deliberate fallback test, not the primary source-informed comparison.

Preflight performs two public GETs (`/login` and `/v3/api-docs`) and reports availability. It identifies itself as `exploratory-testing-skills/1.0`; an earlier default urllib identity received edge 403 responses while curl and the identified client succeeded. A client-specific rejection is not proof that the application is unavailable to ordinary users. Preflight does not log in or verify application correctness. Optional browser tasks inspect public login UI, keyboard/focus, layout, and passive network observations without submitting forms. API tasks are limited to public behavior and unauthenticated product/cart access; OpenAPI may supply context but documentation auditing is excluded. The generator does not accept an arbitrary target override.

For deeper authenticated exploration, use a separately authorized disposable deployment, dedicated accounts, a mutation/cleanup scope, and appropriate time/request limits. Define that as a new profile/task; do not repurpose the hosted public task to sign in or send writes. Do not apply seeded mutations to either hosted deployment. Live findings require manual adjudication and have no known complete bug oracle.

The local profile requires an already running stack. If absent, record a blocked run or start a dedicated deployment under its own operational instructions; this harness deliberately does not execute a generic `docker compose down -v` or reuse shared mutable fixtures.

## Relationship to the real stack

The sample's behavior was grounded in these reviewed repositories:

- Awesome LocalStack at `4731172613d64b8d6b27bc74204f3fda3d0c16e5`: lightweight gateway and separate stable/disposable hosted profiles.
- Backend at `8cb264a24ef997d635210bc5d0152363f78f8486`: cart routes, update/remove semantics, stock checks, and totals. The local checkout also had uncommitted contract-documentation changes; they were not copied into this sample or treated as a deployed revision.
- Frontend at `41e177a6e4b4f53ffb75d0e37b0666dcb9508277`: cart UI, server refresh, and quantity/total presentation.

Authoritative deployment instructions remain in [Awesome LocalStack](https://github.com/slawekradzyminski/awesome-localstack) and its [profile guide](https://github.com/slawekradzyminski/awesome-localstack/blob/4731172613d64b8d6b27bc74204f3fda3d0c16e5/docs/PROFILE_URLS.md). Hosted availability and configuration can change; date each observation and do not turn a live result into a frozen expected behavior.

## Recorded results

Reviewed, sanitized results can be committed under [results/](results/). Keep raw run workspaces, credentials, browser storage, and unreviewed traces out of Git. Record the fixture/skill hashes, model when known, runner/tools, prompt, grading rationale, and material limitations. Do not describe this sample as a hidden benchmark once evaluators have seen its answers.

The [completed September 12 retry assessment](results/2026-09-12-retry.md) records 16 fresh runs, a condition-blind review of the 12 sample reports, and source-backed hosted API/UI comparisons. Both conditions identified both seeded defects; primary artifact scores averaged 11.75/12 with skills and 10.0/12 without. This is a small development pilot, not evidence of a general bug-discovery improvement. The [initial result](results/2026-09-12.md) preserves the earlier usage-blocked attempt.

The [practical extension assessment](results/2026-09-12-usability.md) exercises all eight added cases plus two targeted corrections. It preserves an excessive-retry failure and an incomplete source handoff, then records the fresh revised-skill outcomes.

The separate [historical-project runner](history-study/README.md) uses real before/fix Java/React revisions, a normal request/template/skill comparison, corrected controls and an unavailable API. Its [September 12 closeout](results/2026-09-12-history-study.md) is incomplete and ungraded; it must not be cited as a completed effectiveness result. The optional Claude runner passed Sonnet 5 setup checks but has no candidate comparison results.
