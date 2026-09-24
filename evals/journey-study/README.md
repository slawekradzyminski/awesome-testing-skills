# Dispatch Desk: three-condition screening study

The [completed 24-run assessment](../results/2026-09-12-journey-study.md) found no demonstrated effectiveness advantage for the full skill. All three conditions established every seeded opportunity with actionable evidence.

The later [Claude Opus 5.5 four-arm API pilot](../results/2026-09-24-claude-ablation.md) separates investigation and reporting guidance and uses an audit-based observation score. It is a development check on this same known-ceiling fixture, not an independent effectiveness result. See its [protocol and runner](claude-ablation.md).

This study compares a normal testing request, a reporting template, and the complete exploratory skill on broader API/UI journeys. Read the [frozen protocol](protocol.md) for conditions, expected evidence, scoring and limitations. That document and the controller are evaluator-only material.

The corrected [application](app/) is a disposable Python standard-library server with a browser interface. Defective variants introduce cumulative over-refunding, stale address updates, partial batch writes, stale UI responses, misleading save feedback and a keyboard access barrier. These faults are intentionally present only in isolated candidate copies. The app performs no real payments or external calls and binds to loopback. Keep this fixture local.

## Fixture verification

Requires Python 3 and Playwright CLI with a working browser:

```sh
python3 -m unittest discover -s evals/journey-study/app -v
python3 evals/journey-study/check_fixture.py --out /tmp/dispatch-fixture-check
```

The second command checks every seeded mechanism and corrected variant through HTTP or ordinary browser interactions, retains evidence and closes owned resources. It is known-answer infrastructure validation, not an agent result.

## Run the screening study

Requires an authenticated Codex CLI with the protocol's model available. The runner uses the CLI's existing authentication, per-process configuration overrides, and the shared installed Playwright CLI helper. It does not modify user configuration. Review the protocol and runner before executing: they start 24 fresh model sessions with up to three running concurrently.

```sh
python3 evals/journey-study/study.py prepare --out /tmp/dispatch-study
python3 evals/journey-study/study.py run --out /tmp/dispatch-study --workers 3
```

Preparation freezes source, skills, the reporting template, protocol, schedule and hashes. Supply a fresh output directory; existing runs are never overwritten. Each candidate gets its own directory, loopback server and browser session. The candidate is explicitly confined to those resources, but the runner uses broad local shell permissions for browser compatibility. This is not an operating-system sandbox; inspect retained traces for compliance before accepting results.

Each run retains the candidate report/evidence and controller event stream, runtime audit, resource metadata and preservation checks. The controller stops its own fixture and browser session. A runner timeout or service error is retained as such. The metadata does not automatically score semantic correctness, browser causality, severity or false positives; review those against the protocol. Do not publish unreviewed raw traces or treat fixture checks as evidence of skill effectiveness.

## Review and aggregate

After all runs finish, prepare six batches of four reports with condition labels withheld. Candidate text can still reveal guidance use, so this is a partially masked artifact review, not guaranteed blinding. The review runner starts six additional fresh model sessions and does not rerun the application:

```sh
python3 evals/journey-study/review.py prepare --source /tmp/dispatch-study --out /tmp/dispatch-review
python3 evals/journey-study/review.py run --source /tmp/dispatch-study --out /tmp/dispatch-review
python3 evals/journey-study/aggregate.py --source /tmp/dispatch-study --reviews /tmp/dispatch-review --out /tmp/dispatch-results.json
```

Reviewers see requirements, candidate artifacts, server audits and the frozen rubric. They do not receive the condition mapping, other batches or the original conversation. Keep their raw decisions and document any later adjudication separately. The optional `aggregate.py --adjudications /path/to/decisions.json` input applies explicit decisions while retaining the raw summary; see the archived [adjudications](../results/2026-09-12-journey-study/owner-adjudications.json) for the format. Aggregation requires every case exactly once and valid per-finding scores; it does not use keyword matching to decide whether a bug was found. [Aggregation checks](test_aggregate.py) cover recall denominators, eligibility for triage credit and invalid scores.

The shared task says to save `report.md` and evidence under `evidence/`; that wording permits more than one report location. Review uses the root report when present, otherwise `evidence/report.md`. The controller's original `report_exists` field checks only the root and is not itself proof of a missing deliverable. Both locations receive the same semantic review.

The six-minute budget includes context reading and reporting. The runner has a thirty-second process-exit grace, recorded separately as a budget overrun if used. A longer run is not quietly credited as a faster or better result. API requests are audited; browser-action counts require trace review. Token usage is whatever the CLI exposes, not a measured monetary cost.

This is a small screening study using one new, self-authored application and two repetitions per cell. It can reveal useful differences or ties, but it cannot establish broad reliability or independently held-out performance. Keep its results separate from the original 18-case benchmark and historical scores. Documentation-only findings remain excluded.
