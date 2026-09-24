# Dispatch Desk administrative API release assessment

## Session

**Assessment: no confirmed defects or release blockers found in the administrative API scope tested.** The observed API behaviour supports release against the assessed requirements. This is a bounded assessment, not certification of the browser journey or production security.

Assessed on 12 September 2026, approximately 11:09–11:12 UTC, using only the supplied candidate and `http://127.0.0.1:57593`. Reviewed `app/requirements.md`, `app/domain.py`, `app/app.py`, and the existing domain tests. Source fingerprints are in [source-manifest.json](source-manifest.json); the runtime did not expose a build identifier, so source/runtime identity was not independently established.

Four existing tests passed. Additional live HTTP verification produced **89 passing checks, zero failures, across 90 API requests** (including one preliminary curl). Browser actions: zero. No supplied source, tests, requirements, or guidance were changed. No external services, delegation, or additional server instances were used.

Evidence: [existing tests](existing-tests.txt), [assessment script](assess_api.py), [check results](checks.json), [request index](request-index.md), and [full HTTP request/response records](http.jsonl). The script is assessment evidence and assumes the original fixtures; do not rerun against the mutated instance without an owner reset.

## Findings

**No confirmed product defects.** No unresolved failure or specific defect suspicion remains from the executed checks. There are therefore no defect IDs, severities, workarounds, or repair retests to report. Recommendations below are coverage improvements, not defects.

## Coverage and handoff

Expected behaviour was taken from the supplied product brief. Checks combined response status with subsequent reads of stored state where correctness depended on preservation or persistence.

| Risk / operation | Observed result |
| --- | --- |
| Customer isolation | Alice and Bob lists contained only their own orders. Missing and unknown fixture identities received 401 on reads and every write operation. Cross-customer detail reads, refunds, address edits, notes, and services received 403 in both directions. Full snapshots remained unchanged after these attempts. |
| Cumulative refunds | A100 accepted 3,000 and 2,000 cents; a further 5,001 returned 409 and left the total at 5,000. Two concurrent 3,000-cent requests produced one 200 and one 409. The exact 2,000-cent remainder succeeded; another cent returned 409. Final total: exactly 10,000 cents paid. Zero, negative, boolean, fractional, string, and null amounts returned 400. |
| Address lost updates | A 120-character address saved with version 1. A second save using version 1 returned 409 and preserved the new address/version. Two concurrent saves using version 2 produced one 200 and one 409; the stored address matched the winner at version 3. Blank, 121-character, nonstring addresses and boolean, fractional, or missing versions returned 400. |
| Batch atomicity | Valid-first and invalid-first batches containing a foreign or nonexistent order returned 403/404 with Alice's orders unchanged. A valid two-order express update persisted. Empty lists, nonstring IDs, a nonlist IDs field, and unsupported service returned 400. Services were restored to standard. |
| Notes and rejection preservation | A 160-character note saved. Empty, blank, 161-character, and boolean notes returned 400. `LOCKER:` and whitespace-prefixed lowercase `locker:` instructions returned 422 with actionable error text. The saved 160-character note survived all these rejections. Original note restored. |
| Request parsing and missing resources | Invalid JSON syntax, array/null/string top-level JSON, invalid UTF-8, and an oversized body returned 400. Refund, address, and note writes to a nonexistent order returned 404. Final snapshots showed only the expected refund/version changes. |

Source review corroborated the observed protections: strict integer checks for money/version, cumulative balance validation, address version comparison before mutation, validation of the entire service batch before applying changes, and a server lock around domain operations. Existing tests exercise only one routine example per operation and do not provide the same regression protection as this assessment.

**Useful next work:** retain automated integration cases for cumulative and concurrent refunds, stale and competing address saves, mixed valid/forbidden/missing batches, rejection state preservation, and the two-user authorization matrix. Assert both status and final state. Concurrent scenarios here were each exercised once with two client threads; sustained contention, multi-process deployment, exhaustive input combinations, and transport fault injection were not assessed. Browser order-switch races, draft feedback, keyboard use, and responsive layout remain outside this administrative API assessment. Production authentication, real payments, and general hardening were excluded by the task.

**Cleanup:** all addresses, notes, and services match the baseline; Bob's order is unchanged. A100's refunded counter changed from **0 to 10,000 cents**, and A200's address version changed from **1 to 4**. These cannot be reversed through the authorized API. The fixture owner must reset the instance before another baseline-dependent run. See [baseline](baseline.json) and [final state](final-state.json). No browser session was created, and no server was stopped.
