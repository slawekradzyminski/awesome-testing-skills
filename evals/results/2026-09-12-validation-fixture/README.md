# Orders/profile fixture validation — September 12, 2026

This is infrastructure evidence for four new benchmark cases, not an agent evaluation. No fresh agent trials or effectiveness scores were produced. The existing historical agent results are unchanged.

The maintained [app](../../validation-app/) is derived from the archived [original demo](../../../docs/validation-fixture/server.py). It adds corrected controls, isolated state, bounded input handling, ready-file lifecycle and HTTP auditing. The harness applies the ownership or Cancel defect independently; other behavior stays at the corrected baseline.

| Check | Result |
| --- | --- |
| API `api-10` / `api-11` | Anonymous/unknown identities get 401, owners get their own records, absent orders get 404. Cross-user reads expose the record in the defect variant and get 403 in the control. |
| Profile API | Valid saves persist and increment the counter; invalid bodies/names return 400 without modifying state. Fresh runs reset state. |
| Browser `ui-06` | Save sets the baseline. Cancel with a valid edit sends one POST and persists `Unsaved edit`; save count becomes 2. Reload confirms the value. |
| Browser `ui-07` | Save sets the baseline. Cancel sends zero POSTs; `Saved baseline` remains persisted with save count 1. Reload confirms the value. |
| Empty-input contrast | Cancel leaves stored state unchanged in both variants; browser form validation masks the faulty submit in the defect variant. |
| Cleanup | Both profiles restored to `Original` and checked after reload; remaining save counts 3 and 2 are recorded. Owned servers and browser sessions closed. |
| Public preflight | `/login` and `/v3/api-docs` returned 200 on both configured public hosts. Four read-only requests; no login or writes. Availability is dated, not guaranteed. |

[Seventeen passing harness tests](harness-tests.txt) include the new API/state checks. [Browser results](browser-results.json) retain the summary; each case directory holds browser commands, HTTP audit evidence, Cancel and restored screenshots. All four screenshots were visually inspected. [Metadata](validation.json) records the fixture hashes and scope.

The documented Docker commands were checked against the upstream repository's setup instructions and Compose configuration. A Docker deployment was not started or runtime-validated in this follow-up. Public preflight establishes reachability only. The [user guide](../../GETTING_STARTED.md) explains local/public setup, source snapshots, grading and cleanup.
