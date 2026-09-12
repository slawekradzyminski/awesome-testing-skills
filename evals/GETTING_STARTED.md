# Run the exploratory-testing benchmark

The benchmark measures whether an agent can investigate application behavior, support findings with evidence, and give useful results when checks pass or access is limited. Documentation-only defects are excluded. A blocked environment must never be reported as passing functional tests.

## Choose a target

| Mode | Application and source | Requirements | What the result means |
| --- | --- | --- | --- |
| Local fixtures | Included [cart](sample-app/), [input validation](course-app/), and [orders/profile](validation-app/) apps | Python 3.10+; HTTP tool; browser tool for UI cases | 18 frozen cases, including seeded defects, corrected controls and limited-access situations |
| Public deployment | [Awesome LocalStack](https://github.com/slawekradzyminski/awesome-localstack), at [awesome.byst.re](https://awesome.byst.re/login) or [aitesters.byst.re](https://aitesters.byst.re/login) | Internet and the agent's HTTP/browser tool; source checkouts for source-informed runs | Observations from a changing, shared deployment; no complete known-bug list |
| Local full application | Awesome LocalStack's Docker deployment | Docker with Compose, available host ports, and the upstream setup guide | Real application exploration on your local instance, separate from frozen fixture scores |

The local fixtures need no Docker, AWS account, cloud credentials or external services. Awesome LocalStack is the separate application's project name. Using its public deployment requires no local stack installation; the agent and evaluation harness still run on your machine. These are shared application targets, not a hosted benchmark runner.

The skill installer distributes skill files only. Clone this repository to obtain the benchmark apps and harness. The public repository can be cloned without GitHub authentication:

```sh
git clone https://github.com/slawekradzyminski/awesome-testing-skills.git
cd awesome-testing-skills
```

The following examples use a POSIX shell and start from this repository root. A preparation command creates a candidate directory and prints its task path; it does not launch an AI agent.

## First local run

Prepare an orders API case in a new directory:

```sh
benchmark_run="$(mktemp -d)/orders-run"
python3 evals/harness.py prepare api-10 --out "$benchmark_run"
```

Preparation copies the application, requirements and selected skill, starts an isolated loopback server on an available port, and records source hashes. All data is synthetic. The candidate task contains the runtime URL and allowed operations.

Open a fresh agent session rooted at the printed `candidate/` directory. Give it this request, substituting the printed path:

```text
Read /absolute/path/to/orders-run/candidate/TASK.md and complete that task.
Use only the assigned candidate directory and runtime. Save the report,
evidence and submission.json as specified in REPORTING.md.
```

Give the session an HTTP client for API cases or an available browser tool for UI cases. The prepared task tells it how to use the copied skill. Keep this guide, case catalog, controller directory, rubric and previous results out of that session: they reveal the expected answers. This separation relies on the runner's context discipline; it is not an OS sandbox.

Once the agent finishes, run these commands yourself, outside its session:

```sh
python3 evals/harness.py grade "$benchmark_run"
python3 evals/harness.py stop "$benchmark_run"
```

Always run `stop`, including after an interrupted or failed trial. It stops only the fixture owned by this run. Review `candidate/report.md`, `candidate/submission.json`, its evidence, and `controller/grade.json` using the [rubric](rubric.md). A passing integrity check is not an automatic quality score. Record the six dimension scores, confirmed functional findings, false positives, unresolved claims, and whether the expected useful outcome was met.

Use `ui-06` instead of `api-10` for the profile browser case. The matching corrected cases are `api-11` and `ui-07`; do not tell candidates which variant they receive. See the [full case catalog](README.md#run-a-case) for cart, validation, clean, source-only, missing-source and unavailable-environment cases.

For a comparison, prepare a new directory with `--without-skill`. Use a separate fresh session without another installed or inherited copy of these skills. Keep model, tools, budget and task scope equal. Repeat and alternate condition order before drawing conclusions. Cases described here are development cases, not unseen effectiveness evidence.

## Run against the public application

Available profiles are:

| Target | API profile | UI profile |
| --- | --- | --- |
| `https://awesome.byst.re` | `localstack-hosted-api` | `localstack-hosted-ui` |
| `https://aitesters.byst.re` | `localstack-sandbox-api` | `localstack-sandbox-ui` |
| `http://localhost:8081` | `localstack-local-api` | `localstack-local-ui` |

Check current availability first:

```sh
python3 evals/harness.py preflight localstack-hosted-api
```

Preflight makes two public GET requests and prints their outcomes. It neither starts the application nor proves it is correct. A failed preflight needs investigation or a blocked report; do not declare functional tests passed.

For the primary source-informed run, obtain the application's sources. The repositories are:

- [Awesome LocalStack](https://github.com/slawekradzyminski/awesome-localstack): deployment and gateway configuration.
- [test-secure-backend](https://github.com/slawekradzyminski/test-secure-backend): backend application.
- [vite-react-frontend](https://github.com/slawekradzyminski/vite-react-frontend): frontend application.

```sh
benchmark_sources="$(mktemp -d)"
git clone https://github.com/slawekradzyminski/awesome-localstack.git "$benchmark_sources/stack"
git clone https://github.com/slawekradzyminski/test-secure-backend.git "$benchmark_sources/backend"
git clone https://github.com/slawekradzyminski/vite-react-frontend.git "$benchmark_sources/frontend"

benchmark_live_run="$(mktemp -d)/public-run"
python3 evals/harness.py prepare-live localstack-hosted-api \
  --out "$benchmark_live_run" \
  --backend "$benchmark_sources/backend" \
  --frontend "$benchmark_sources/frontend" \
  --stack "$benchmark_sources/stack"
```

Run the candidate task in a fresh session and grade it as in the local example, using `"$benchmark_live_run"`. Choose `localstack-hosted-ui` for browser exploration. For an intentional missing-source trial, omit the three source flags and record that condition separately.

The harness snapshots each checkout's committed HEAD and records revisions. Local edits and Git history are excluded; repository HEAD is not proof of the deployed build. Record any source/deployment uncertainty. The [upstream profile guide](https://github.com/slawekradzyminski/awesome-localstack/blob/main/docs/PROFILE_URLS.md) describes the deployment URLs.

All supplied live profiles are **public read-only**, including the shared sandbox and local profile. Their task permits bounded public GET/browser observations; it excludes login/form submission, account creation, emails and data changes. OpenAPI may supply context, but documentation auditing is out of scope. For authenticated or mutating exploration, define a separately authorized isolated task. `stop` does not stop, reset or change any public deployment.

Date live observations and keep them separate from frozen-case recall: the deployment and its known defects can change. No findings is a valid result with meaningful passing evidence and coverage limits.

## Run Awesome LocalStack locally

Use a dedicated checkout and follow the [upstream setup guide](https://github.com/slawekradzyminski/awesome-localstack#lightweight-profile) for Docker prerequisites and port conflicts. The lightweight profile's commands are:

```sh
git clone https://github.com/slawekradzyminski/awesome-localstack.git /path/to/awesome-localstack
cd /path/to/awesome-localstack
docker compose -f lightweight-docker-compose.yml up -d
docker compose -f lightweight-docker-compose.yml ps
```

Return to this benchmark repository and use `preflight localstack-local-api`, then `prepare-live localstack-local-api` or `localstack-local-ui`, with the same source flags as above. Wait for the application to be available at `http://localhost:8081/login` before beginning a discovery trial. The harness manages only its Python fixtures; it does not manage Docker.

After completing the run, stop the dedicated stack from its checkout:

```sh
docker compose -f lightweight-docker-compose.yml down
```

Only stop a stack you started for this run. Do not reset shared state to reproduce a finding. Keep the tested stack revision/image set and source revisions with the result.

## Try the included demo directly

To inspect the orders/profile app without preparing a scored case:

```sh
python3 evals/validation-app/app.py --port 8090
```

Open `http://127.0.0.1:8090/`; the server also prints its address. Stop it with Ctrl+C. This starts the corrected base app; the harness creates the defect variants for benchmark cases. Restarting resets the scratch profile. The [original smoke-test app](../docs/validation-fixture/server.py) and [historical validation](../docs/validation.md) remain archived; use the maintained benchmark app above for new runs.

## Verify the benchmark infrastructure

```sh
python3 -m unittest discover -s evals/tests -v
python3 -m unittest discover -s evals/sample-app -v
python3 evals/check_browser_fixture.py --suite validation --out /tmp/profile-fixture-check-001
```

The browser check requires Playwright CLI and its browser. Use a fresh output path. It checks the known profile mutation/control with real clicks, captures evidence and closes its own sessions. Passing these infrastructure checks does not establish agent bug-finding effectiveness. Keep new run workspaces private until their evidence and source snapshots have been reviewed for sharing.
