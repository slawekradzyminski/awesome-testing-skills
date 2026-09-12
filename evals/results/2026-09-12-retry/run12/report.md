# Cart editor exploration

Runtime-only session on 2026-09-12 at http://127.0.0.1:64185. Source access was explicitly unavailable; source revision and deployed build are unknown. The Codex in-app browser was used at 1280×720 and 375×812 CSS pixels, with disposable Alice/Bob identities. Browser version and zoom were not measured; no throttling or mocks were applied.

Charter: verify provisional edits, explicit Save, Cancel, visible totals and feedback within the existing-cart feature. Prioritize unwanted persisted changes, stale totals, identity boundaries and invalid-input recovery. Stop within five minutes / 60 API requests / 45 browser actions. Checkout, adding removed items and production authentication are outside scope.

## Confirmed finding: Cancel saves valid edits (UI-1)

**Severity: High (provisional).** Cancel changes saved cart data, directly violating the core explicit-save contract. On Alice's initial cart (quantity 1), Edit → quantity 3 → Cancel closed the form, displayed “Cart updated”, and showed quantity 3 / total 36. An independent GET confirmed the persisted value. Reopening Edit showed 3. At narrow width, changing saved quantity 2 to 4, tabbing to Cancel and pressing Enter reproduced the changed total 48 and reopened value 4.

Expected: Cancel leaves saved quantity and total unchanged and makes no update request (requirements.md UI-1). Impact: users unintentionally save an edit they chose to abandon. Workaround: explicitly Save the prior value. No checkout consequence was tested. A default form submission is a hypothesis only; source and browser mutation traffic were not inspected.

The invalid-input contrast (quantity 6 → Cancel) displayed “Edit cancelled” and retained the visible saved value. Normal Save 3→2 updated both UI and independently read API total correctly. These contrasts narrow the failure to valid Cancel edits in the observed paths, rather than all editor exits.

Evidence: [ordered reproduction](evidence/reproduction.txt), [API observations](evidence/http.json), [desktop failure screenshot](evidence/cancel-saved.png), [narrow focused Cancel screenshot](evidence/narrow-editor.png). Both screenshots were opened and visually inspected.

Retest: from saved quantity 1, cancel a valid edit to 3 via pointer and keyboard; assert editor closes, no PUT occurs, GET remains 1/12, and reopening shows 1. Repeat with invalid quantity, then confirm Save remains functional.

## Risk map and coverage

| Journey / risk | Priority and impact | Observation | Remaining experiment |
|---|---|---|---|
| Valid Cancel | High: unintended saved changes | Confirmed twice, pointer and keyboard | Trace request count and fix/retest forbidden mutation |
| Save and visible totals | High: misleading cart state | Save to 2 showed 24; independent GET agrees; restore to 1 showed 12 | Pending response/race behavior |
| Quantity and stock rejection | Medium: corrupt cart | Direct API rejected negative, fraction, null, string, boolean and missing with 400; 6 with 409; final cart unchanged | Five-unit boundary and resettable zero-removal fixture |
| Identity boundary | High: wrong user's cart | Anonymous GET 401; Alice edits left Bob 2/24; UI role switch showed Bob 2/24 | Account switch during pending save; wider authorization tests |
| Narrow layout and keyboard | Medium: inaccessible flow | 375×812 controls and labels visible; focus outline on Cancel; Tab/Enter Save and Cancel reachable | Full keyboard-only journey, screen reader, other browsers |
| Error recovery | Medium: trapped editor | Save 6 showed native max-5 validation; correcting to 1 and keyboard Save worked | Server error and connection failure UI recovery |

[Invalid Save screenshot](evidence/invalid-save.png) was opened and inspected. No clipping or control overlap was observed in these sampled states. Browser warning/error reads were empty; this is not a comprehensive console or network audit. API validation evidence and UI validation evidence are separate channels.

## Limits, cleanup and budget

No implementation or tests were inspected or modified. Browser-generated API traffic was not instrumented, so exact automatic request counts/statuses and Cancel PUT count are unknown. The saved side effect is established by a separate authenticated read. 17 direct API requests are recorded in http.json. There were 25 browser control actions including tab creation/close and viewport changes (observations excluded); no automated repeated polling or reloads. Token/usage metrics are unavailable.

Zero removal was intentionally left for a resettable fixture because adding removed items is out of scope. Delayed-response races, complete authorization coverage, real devices, cross-browser behavior, performance and screen readers remain open. Invalid API requests were checked with a final unchanged-state read rather than independently reading after each invalid request.

Alice restored to initial quantity 1 / total 12 through UI Save; Bob remained 2 / 24. Final API reads verified both. Viewport override reset and created tab closed. No leftovers beyond the report, submission and evidence. Next useful action: capture browser requests for the valid Cancel reproduction, then inspect the editor event handling with source access.

Session start: 2026-09-12T08:40:37+00:00. Report written: 2026-09-12T08:44:43.051731+00:00. Elapsed through report write: 246.1 seconds.
