# Cart editor exploration

Session: 2026-09-12, started 08:31:42 UTC. Target: http://127.0.0.1:64178. Charter: verify provisional quantity edits, explicit Save/Cancel, totals, and nearby validation and identity boundaries. Stop within five minutes, 60 API requests, and 45 browser actions. No application fixes were made.

## Result: Cancel commits valid edits (UI-1)

**Confirmed functional/network defect; Medium severity.** Cancel changes saved cart quantities despite the explicit discard requirement. A valid cancellation produces “Cart updated” feedback and updates visible totals. This can cause unintended cart changes. One desktop mouse reproduction and one narrow keyboard reproduction succeeded; an invalid-input contrast did not save.

Reproduction on Alice:

1. Start at quantity 1 / total 12. Edit to 3, click Save. The UI shows quantity 3 / total 36; reopening Edit shows 3.
2. Edit to 4, click Cancel. Expected: no PUT, quantity remains 3, reopening Edit shows 3.
3. Actual: PUT `/api/v1/cart/items/1`, body `{"quantity":4}`, status 200, followed by GET 200. The form closes, summary becomes quantity 4 / total 48, and status says “Cart updated.”
4. Reload and reopen Edit: saved value is 4. Thus this is persisted behavior, not just a stale label.
5. At 375 × 740, edit 4 to 2, Tab to Save, Tab to Cancel, Enter. Actual: another PUT 200 plus GET 200, quantity 2 / total 24. A separate HTTP read confirms persisted quantity 2.

Evidence: [before network](evidence/network-before-cancel.txt), [after network](evidence/network-after-cancel.txt), [request body](evidence/cancel-request-body.txt), [response body](evidence/cancel-response-body.txt), [UI snapshot](evidence/cancel-valid-snapshot.txt), [final network](evidence/network-final.txt), and [independent HTTP reads](evidence/http.json).

The following screenshots were captured **and opened/visually inspected**:

- [Desktop result, 1280 × 720](evidence/cancel-desktop.png): Alice quantity 4, total 48, “Cart updated” after Cancel.
- [Narrow keyboard focus, 375 × 740](evidence/narrow-cancel-focused.png): provisional 2 while saved summary remains 4; Cancel has a visible focus outline. Controls and text fit.
- [Narrow keyboard result](evidence/narrow-after-keyboard-cancel.png): summary changes to 2 / 24 and feedback says “Cart updated.”

Source mechanism: `app/static/index.html` defines Cancel inside the form without `type="button"`. In `app/static/app.js`, the click listener hides the form but does not prevent the button's submit default; the form submit handler sends PUT. This agrees with the live behavior. No injected handlers, DOM changes, forced clicks, or network mocks were used.

Contrast: entering 6 and clicking Cancel hid the form, displayed “Edit cancelled,” and left quantity 4 unchanged. Comparing cumulative requests showed no new API request during that action. Browser console reported “An invalid form control with name='quantity' is not focusable.” This is consistent with validation running after the handler hides the form; it is recorded as supporting evidence, not a separate user-facing defect. [Contrast snapshot](evidence/invalid-cancel-snapshot.txt), [contrast network](evidence/network-invalid-cancel.txt), [console](evidence/console.txt).

Regression recommendation: valid mouse and keyboard Cancel must send **zero PUTs**, preserve the previous total and persisted quantity, and reopen with the saved value. Include invalid/empty provisional input and keep a successful Save contrast.

## Risk map and coverage

| Journey / state | Source evidence and impact | Existing protection / uncertainty | Experiment and outcome / next probe |
| --- | --- | --- | --- |
| Cancel valid edit | Implicit submit button can write discarded data; highest priority | Existing tests cover only domain operations | Confirmed twice; fix button behavior then retest forbidden PUT side effects |
| Save and totals | PUT then refresh must agree with persisted cart | Domain test checks quantity 3 -> total 36 | Save 1 -> 3 worked, acknowledgement and reopened quantity checked; Cancel's totals also matched independent saved state |
| Invalid quantities and stock | API must reject malformed quantities without mutation | Strict integer check and stock check; one stock unit test | Direct requests for -1, 1.5, missing, null, string, boolean returned 400; 6 returned 409; each followed by GET showing unchanged quantity 2 |
| Identity isolation | Header identity selects cart | Domain test checks other identity unchanged; production authentication excluded | Anonymous GET returned 401; Bob stayed 2 while Alice changed. Bob UI switching and mutation were not exercised; medium residual risk |
| Narrow keyboard flow | Focus and controls must remain usable | Explicit input focus and CSS focus outline | Tab navigation to Cancel worked at 375 × 740; Cancel activation reproduces defect. Full keyboard Save/error recovery remains untested; medium residual risk |
| Async identity switching / delayed saves | Refresh writes shared `current`; no generation check or disabled pending controls | No async/browser tests present | Not experimentally exercised; medium residual risk. Next: deliberately delay Alice response, switch to Bob, and compare displayed identity with saved cart |
| Removal / zero | Domain deletes existing item; re-add is excluded | No existing zero unit test | Not exercised to retain recoverable fixture state. Next: owner-resettable fixture, save zero, verify empty totals and behavior afterward; medium residual risk |

## Environment and evidence limits

Inspected all supplied app source files and the two relevant existing domain tests. Executed `python3 -m unittest discover -s app -p test_domain.py`: 2 passed ([output](evidence/tests.txt)). No browser regression suite was present among the supplied application files. Missing tests are not reported as defects.

Source revision is unknown; [SHA-256 source fingerprints](evidence/source-sha256.txt) identify the inspected files. `/health` reports deployed `sample-1`; no deployment digest was available, so an exact source/runtime match is unverified. Browser: HeadlessChrome 152.0.0.0 on macOS; [browser observation](evidence/browser.txt). Sampled desktop 1280 × 720 and narrow 375 × 740. No throttling, mobile emulation, or zoom changes were applied. This does not establish real-device, Safari, screen-reader, exhaustive accessibility, latency, or race coverage. Failed tooling experiments were a mis-shaped run-code callback and a stale element reference after reload; neither is an application defect.

## Cleanup and budget

Restored Alice to quantity 1 / total 12 using the authorized API and verified by fresh GET. Bob remained quantity 2 / total 24. Product stock remains 5. See final entries of [HTTP evidence](evidence/http.json). No item was removed. Closed only browser session `retry04`; server lifecycle remains with its owner. No mocks or interceptors were installed.

Counted 38 browser CLI invocations including snapshots, network inspections, screenshot captures, the failed callback and stale-ref click, and session close; this conservative count is below 45. Browser generated 8 API requests. HTTP script generated 22 requests, including one `/health`, so total is 29 `/api/` requests, or 30 counting health. Static page resources are excluded. Elapsed time is recorded in `evidence/session.json`; no unavailable token/usage metrics are claimed.

Outstanding: retest the confirmed Cancel defect after a fix; prioritize delayed identity/Save handling, complete keyboard Save/error recovery, Bob UI switching, and zero removal in a resettable fixture. Application, requirements, skill, and existing tests were not edited.
