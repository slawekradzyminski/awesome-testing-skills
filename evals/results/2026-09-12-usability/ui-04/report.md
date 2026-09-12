# Cart editor exploration

No confirmed discrepancies were observed in the sampled flows. This is a bounded runtime assessment, not a defect-free verdict. The highest remaining uncertainty is Cancel's forbidden network side effect: persisted state was unchanged, but browser requests were not captured.

## Charter and environment

Explore provisional editing, explicit Save/Cancel, visible totals, error recovery, keyboard use, and fixture isolation. Stop within five minutes, 60 API requests, and 45 browser actions. Assigned runtime: http://127.0.0.1:49526/. Session date: 2026-09-12. Source access was explicitly unavailable; source revision/deployed build unknown. Chrome browser agent; desktop capture 1728×907 pixels and explicit narrow viewport 375×812 CSS pixels. Exact Chrome version and desktop CSS viewport were not collected. No mocks or throttling.

## Observed outcomes

| Journey / risk | Observation | Outcome |
|---|---|---|
| Draft accidentally saved on Cancel | Changed Alice 1→3, Cancel; independent GET remained 1 / 12; reopen showed 1 | State preservation passed; request absence unverified |
| Save persistence and totals | Keyboard Save 3, “Cart updated”, total 36; GET and reload confirmed | Passed |
| Narrow keyboard and recovery | 375×812: keyboard editor, max-5 validation on 6, keyboard Cancel, reopen 3, keyboard Save 1 | Passed sampled journey |
| Invalid API input | -1, 1.5, missing, null, string, boolean each 400; GET after each stayed unchanged | Passed |
| Stock bound | Direct PUT 6 returned 409; GET unchanged | Passed |
| Identity isolation | Alice Save left Bob 2 / 24; anonymous GET returned 401 | Passed sampled cases |

Screenshots were captured and actually opened: [desktop Cancel](evidence/cancel.png), [desktop Save](evidence/save.png), [narrow validation](evidence/narrow-error.png), [narrow restored cart](evidence/narrow-restored.png). The narrow card, totals, and success feedback fit the viewport. Native validation temporarily overlapped the buttons; keyboard Cancel remained usable. No impairment was established from that transient overlap.

Detailed ordered interactions and accounting: [UI log](evidence/ui-session.md). Independent request/response records: [HTTP evidence](evidence/http.json). The direct API requests corroborate persistence; they do not substitute for the actual UI Save/Cancel actions, which were exercised through ordinary controls.

## Remaining risks and next useful checks

- Medium: instrument browser traffic around both valid and invalid Cancel and assert zero update requests. Unchanged data alone cannot prove this.
- Medium: exercise an actual server error and delayed Save through the UI. The visible overstock error here was native input validation; the separately tested 409 did not traverse UI error handling.
- Medium: with a resettable fixture, test zero removal and Alice/Bob switching while a provisional edit is open. Removal was skipped because adding removed items is outside scope.
- Lower: validate quantity 5, repeated rapid Save, additional browsers/devices, focus after Save, and assistive technology behavior. These were not established defects.

Suggested regression scenarios: valid Cancel preserves saved value and issues no PUT; keyboard Save updates quantity × 12 and survives reload; invalid Cancel works without server mutation; API invalid-type/overstock rejection preserves cart; edits remain isolated across Alice/Bob.

## Limits, accounting, and cleanup

27 state-changing browser operations plus 12 accessibility snapshots and four screenshots (43 combined). 23 direct API requests are recorded; browser-generated traffic was not instrumented, so exact combined requests cannot be certified. Only two page loads, two successful UI Saves and one invalid Save attempt were performed; no retries or availability failures. No production authentication, checkout, adding items, full accessibility audit, or performance assessment was attempted.

Alice was restored through the UI to quantity 1 / total 12. Final independent GETs confirm Alice 1 / 12 and Bob unchanged 2 / 24. The temporary viewport was reset and only the created tab was closed. No application, requirements, skills, or tests were changed. Outstanding checks are listed above; no fixture cleanup remains.
