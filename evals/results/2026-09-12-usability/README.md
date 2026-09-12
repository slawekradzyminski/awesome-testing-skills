# Practical-case evidence archive

This archive preserves the original tasks, reporting contracts, reports, structured submissions, candidate evidence, server audits, fixture/skill hashes, and owner review decisions for the usability extension. These were fresh with-skill agent trials, not a new with/without effectiveness comparison. Initial failures and targeted revised-skill reruns are separate directories; do not discard the failures when reporting results.

Each `review.json` assesses whether the expected useful outcome was met. Each `grade.json` checks artifact integrity and corroborated request facts. These are different decisions: a well-formed report can omit an important handoff, while an honest blocked report can still violate the retry budget. Read the reasons, not just the booleans.

Temporary paths and localhost URLs inside evidence are historical locators. Fixtures have been stopped after review. Recreate runs with the harness instead of running archived scripts against those addresses. All registration and credential values were synthetic. App and skill snapshots are represented by hashes; the baseline source remains in the repository and mutations are frozen in the harness.

The owner reviewed every report and structured submission, selected decisive HTTP/body/state records and source evidence, all server audit summaries, and representative UI screenshots. This extension was not condition-blind; it was intended to expose practical weaknesses and verify narrow corrections. Exact model version, full tool traces, token/cost measurements and automatically enforced wall-clock budgets are unavailable. Candidate isolation uses fresh contexts and task boundaries, not an OS sandbox.

The 14-test infrastructure log includes expected negative-test grade errors followed by the successful unittest summary. Those deliberate invalid submissions are validator tests, not failed agent reports. The actual initial API outage run separately failed its retry-budget check.
