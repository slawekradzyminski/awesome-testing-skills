# Claude Opus 5.5 four-arm API ablation — development pilot protocol

Status: protocol, not results. Evaluator-only; never give this file or `claude_ablation.py` to candidates.

**This pilot cannot establish skill superiority.** It reuses the self-authored Dispatch Desk API defective fixture as a development and calibration case. That fixture has a known ceiling: in the [three-condition study](protocol.md), every condition established all three API seeds. The study author knows the seeded mechanisms, and there is no held-out case, corrected control, or enough repetitions to estimate reliability. Use this pilot to check the harness, arm construction, scoring, cost, and whether any arm falls below the ceiling. It does not rank the arms.

## Question and arms

Which components of the API skill change runtime-evidenced discovery for one model? Every arm uses the same model (`claude-opus-5-5` requested, effort `high`), Claude Code CLI, tools, business requirements, defective fixture, budget, and freshly started runtime:

1. **normal:** the base release-readiness task only.
2. **report-only:** the base task plus `guidance/SKILL.md`. That file contains the skill's title and introduction, the *Evidence, findings, and completion* section, and `references/reporting.md`.
3. **investigation-only:** the base task plus `guidance/SKILL.md`. That file contains the same title and introduction, the *Establish the target*, *Read code*, and *Explore the running API* sections, and `references/experiment-design.md`.
4. **full:** the base task plus the complete, verbatim skill directory, including frontmatter and both references.

The three guided arms receive the same instruction line. The partial texts are cut deterministically from the frozen `SKILL.md` by section heading. Preparation fails if the headings change or if a link does not resolve. The split is a section-level ablation, not a sentence-level one: the introduction appears in both partial arms, and the investigation sections keep a few incidental sentences about reporting (for example, reserve time for a usable report). Only the full arm has frontmatter.

## Design and isolation

The default is two Williams-square blocks of four runs (8 runs), with one worker. `--repeats 4` completes the square: each arm then occupies each position once and follows each other arm once. The API surface only is tested: there is no browser, UI, or corrected-control arm.

`prepare` freezes the following:

- the corrected app (seeds R1–R3 from `study.mutate` are applied per run)
- each arm's guidance and task template
- this protocol and the schedule
- SHA-256 hashes of all of the above, plus the controller and `study.py`
- the git revision and any uncommitted skill/study paths
- the Claude Code version, the requested model, the tool list, and the budgets

`run` refuses to start if any frozen input or the controller changed.

Isolation follows `study.py`. Each run has its own candidate directory with the app, its guidance if any, `TASK.md`, and `evidence/`. It also has its own loopback fixture. The controller audit and logs live outside the candidate directory. Claude Code runs as follows:

- Flags: `--bare` (API-key authentication, with no hooks, CLAUDE.md, plugins, or auto-memory), `--disable-slash-commands`, `--strict-mcp-config`, and `--no-session-persistence`.
- Environment: a fresh `CLAUDE_CONFIG_DIR`, and inherited `CLAUDE*`/`ANTHROPIC_*` overrides removed (their names are recorded).
- Tools: only `Bash, Read, Write, Edit, Glob, Grep`. There is no delegation or web tool.
- No fallback model.

Permissions are bypassed so shell tools work. This is a context boundary, not an operating-system sandbox. Tool-input path heuristics are recorded as `boundary_flags`, and a person must review them. The output directory must be outside the repository.

Limits: 6 minutes including reporting, 120 `/api` requests, a 390 s hard stop, and a frozen `--max-budget-usd` cap. Runs over time or over the request budget are flagged, not excluded. Failed, timed-out, or capped runs stay in the denominator with their status. Never quietly replace them.

## Recorded per run

- Arm and schedule position.
- Model: the requested ID, the init-reported model, the model IDs in usage, and a mismatch flag.
- Claude Code version.
- Cost: `total_cost_usd` (a client-side estimate, not a bill), token usage, per-model usage, turns, and durations.
- Prompt hashes: the rendered task, the template, the stdin prompt, and the guidance.
- The exact command.
- The request audit: count, status histogram, budget flag, and malformed lines.
- App and guidance preservation.
- Runner status and exit code, and whether the fixture was still running at the end.
- Elapsed time.
- Tool-call counts and boundary flags.
- The report's existence, hash, and size.
- The audit score.

Raw stream-JSON events, stderr, final text, the audit, and the server log are kept.

## Primary outcome: audit-observed seeds (0–3)

The controller scores deterministically from the ordered request/response audit (`score_audit`). It does not depend on which order IDs, amounts, or read route the candidate chose. A seed counts only when a **successful follow-up read** (`GET /api/orders/{id}` or `GET /api/orders`), logged after the violating request, **shows the violated state**. Triggering the write without observing its result earns no primary credit. Triggering is recorded separately.

| Seed | Triggered by | Observed when a later read shows |
| --- | --- | --- |
| R1 | An accepted refund, at least the second on that order, whose response has `refunded > paid` | That order with `refunded > paid` |
| R2 | An accepted address save that sends a version the order really held but that is lower than its current version, replacing a different newer address | That order's address equal to the stale value, not the overwritten one |
| R3 | A rejected (≥400) service batch whose accessible prefix, before the first missing or forbidden ID, contains an order whose service would change | That prefix order with the batch's service, although no accepted write set it |

The expected state starts from the fresh fixture. It is updated only by the intended fields of accepted writes, so a legitimate later write is not credited as a partial batch. Audit order is reply order. Only traffic to the candidate's runtime counts: calls to the domain code in-process, or traffic to another server, earn nothing. Recompute the score with `python3 claude_ablation.py score --audit <audit.jsonl>`.

**Report wording is never used in the primary score.** Report content, triage quality, and false positives may be reviewed afterwards as clearly labelled secondary observations, using the frozen [three-condition rubric](protocol.md).

## Interpretation fixed in advance

Report per-run values by arm, with no pooled significance test and no omnibus score. All arms at 3/3 is the expected ceiling result and says nothing about the value of the components. An arm below the ceiling indicates a problem worth investigating on new, held-out cases; it does not establish that any arm is better. Any claim of skill superiority needs a separately frozen study on held-out fixtures, with controls and enough repetitions.

## Commands (not run by preparation or tests)

```sh
python3 -m unittest discover -s evals/journey-study -p 'test_claude_ablation.py' -v
python3 evals/journey-study/claude_ablation.py prepare --out /tmp/claude-ablation
python3 evals/journey-study/claude_ablation.py run --out /tmp/claude-ablation
```

Use an already configured `ANTHROPIC_API_KEY`; never put its value in a saved command or study artifact. Check that the requested model identifier is right before `run`. The resolved model is recorded and never assumed.
