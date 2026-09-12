# Exploratory skill evaluations

This suite evaluates an agent using the API/UI skills. It keeps three kinds of evidence separate:

1. **Infrastructure checks:** does the fixture, mutation application, isolation, and artifact validator work?
2. **Seeded agent evaluations:** can a fresh agent identify a known defect, produce convincing evidence, prioritize risks, and avoid unsupported findings in matching controls?
3. **Real Awesome LocalStack evaluations:** does the skill support useful exploration on an actual deployment with unknown bugs and possible source/build drift?

The first category cannot substitute for the other two. `harness.py grade` performs deterministic integrity checks; an evidence-based review using [rubric.md](rubric.md) decides the testing-quality result.

## Kept sample repository

[sample-app](sample-app/) is a small self-contained application that stays in this repository. It requires Python 3.10+ and an available browser agent for UI work. It uses Awesome LocalStack's product/cart route conventions and quantity rules, but has its own implementation, disposable identities, and in-memory state. It is not a copy of Spring, React, SSO, or the production stack. See [requirements](sample-app/requirements.md).

The baseline application is the control. The evaluator-only harness applies one frozen change to an isolated copy: accepting a negative quantity, or allowing Cancel to submit an edit. The agent sees the resulting code when source is available, never a variant flag or the expected finding. The sample's existing tests intentionally cover only a narrow slice of behavior.

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

| Case | Surface | Access | Purpose (evaluator-only) |
| --- | --- | --- | --- |
| api-01 | API | Source + runtime | Detect persisted negative quantity |
| api-02 | API | Source + runtime | Matching control; evaluate restraint and risk assessment |
| ui-01 | UI | Source + runtime | Detect Cancel sending an update and persisting it |
| ui-02 | UI | Source + runtime | Matching control; inspect ordinary Save/Cancel behavior |
| api-03 | API | Source only | Find code-level defect without claiming runtime execution |
| ui-03 | UI | Runtime only | Explore without repeatedly blocking on missing source |

Candidates receive neutral application tasks with a five-minute budget, up to 60 API requests or 45 browser actions. The fixture's server audit corroborates requests; a reviewer checks browser actions, opened screenshots, meaning of findings, and untested claims. The harness currently reports request counts but does not automatically measure browser-action counts or token usage. Record those from the runner transcript when available.

To verify the browser fixture itself, with `playwright-cli` and a browser installed:

```sh
python3 evals/check_browser_fixture.py --out /tmp/browser-fixture-check-001
```

This script clicks Cancel and Save in fresh mutation/control instances, checks persisted state and HTTP writes, saves screenshots/command evidence, and closes its owned sessions and servers. It already knows the expected result, so its success is **infrastructure validation, not a skill score**.

## Actual Awesome LocalStack profiles

[profiles.json](profiles.json) supports local `http://localhost:8081`, stable hosted `https://awesome.byst.re`, and disposable hosted `https://aitesters.byst.re`, each with API/UI tasks. All provided live tasks are **public read-only**. Even the disposable sandbox is shared, so its existence is not permission to reset other users' state.

```sh
python3 evals/harness.py preflight localstack-hosted-api
python3 evals/harness.py prepare-live localstack-hosted-api \
  --out /tmp/localstack-eval-001 \
  --backend /path/to/test-secure-backend \
  --stack /path/to/awesome-localstack
```

For UI source context, add `--frontend /path/to/vite-react-frontend`. Source snapshots are taken from each checkout's committed HEAD; uncommitted changes and Git history are excluded. This preserves the original working trees and records revisions/hashes. Source snapshots may still contain private project information; runs remain local until reviewed for publication. They are not evidence that the deployment uses those commits. With no supplied source, the task explicitly uses runtime-only exploration.

Preflight performs two public GETs (`/login` and `/v3/api-docs`) and reports availability. It does not log in or verify application correctness. Optional browser tasks inspect public login UI, keyboard/focus, layout, and passive network observations without submitting forms. API tasks are limited to the public contract and unauthenticated product/cart access. The generator does not accept an arbitrary target override.

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

The [September 12, 2026 result](results/2026-09-12.md) records passing infrastructure checks and the access/usage limits that prevented independent skill scores.
