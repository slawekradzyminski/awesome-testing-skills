# Cart exploration report

One confirmed high-priority defect: **Cancel saves valid edits (UI-1)**. Alice's quantity changed from 1 to 3 and total from 12 to 36 after clicking Cancel. Independent GET confirmed persistence. At 375 px width, keyboard activation of Cancel likewise changed a saved quantity of 2 to 4, with total 48. Both paths displayed “Cart updated”. This can overwrite a cart that the user intended to leave unchanged.

Expected: Cancel discards the draft, sends no update, and preserves the saved quantity. Reproduction and source mechanism are in [evidence/reproduction.txt](evidence/reproduction.txt). [Desktop screenshot](evidence/after-cancel.png) and [keyboard screenshot](evidence/narrow-keyboard-cancel.png) were opened and inspected. The Cancel button lacks `type="button"`; its click handler hides the form without preventing default submission. Valid input therefore reaches the Save submit handler. This is one defect across two interaction modes, not separate totals and feedback defects.

## Exploration and passing checks

Read the relevant Python server/domain, HTML/JS/CSS, and existing tests. Both existing domain tests passed; [test output](evidence/existing-tests.txt). They cover totals/identity and stock rejection but do not cover UI cancellation.

Direct API probes verified Alice/Bob baselines and isolation during Alice updates; anonymous GET and PUT return 401. Negative, fractional, missing, null, string, and boolean quantities return 400 and each follow-up GET confirms unchanged state. Quantity 6 returns 409 without mutation; quantity 5 succeeds with total 60 and catalog stock remains 5. [HTTP evidence](evidence/http.jsonl) records all 27 direct requests, responses, and purposes.

Normal Save works using keyboard at 375×812: quantity 2, total 24, success acknowledgement; reopening shows 2. Entering 6 and Save produces visible browser validation while leaving the editor open and visible total unchanged. Cancel with invalid 6 closes the editor without the valid-input defect. All four supplied screenshots were actually opened and inspected. At tested desktop/narrow sizes the exercised controls were visible and reachable.

## Remaining risks and limitations

- High: cancellation to zero could remove the existing item. The confirmed default-submit mechanism supports this risk, but zero was deliberately not sent because re-adding removed items is outside scope and fixture restoration would require a server restart. Next probe: zero cancellation on a separately resettable fixture.
- Medium: identity switching while requests are pending may expose stale summaries; handlers use mutable identity/current state. Not reproduced or claimed as a defect. Next probe: controlled response delay while switching accounts during Save/refresh.
- Medium: server/network failure feedback and focus recovery were not exercised. Native browser validation was tested, but it prevented reaching the server's stock-error UI path.
- Limited to the assigned fixture/browser engine and brief desktop/narrow checks; not a full accessibility, concurrency, or browser compatibility audit. No production-authentication claims.

## Budget and cleanup

Exploration and reporting completed in under five minutes (approximately three and a half minutes). 27 direct API requests are logged; 9 additional browser API requests are inferred from exercised paths and inspected source, approximately 36 total, below 60. Browser traffic was not independently instrumented, so the inferred count is not presented as a captured network total. 27 browser state-changing actions including navigation, viewport changes, and tab close; observations/screenshots excluded. No unavailable token or cost metrics are claimed.

Alice restored to quantity 1 / total 12 and Bob verified unchanged at 2 / 24. Final invalid UI draft was cancelled without changing the displayed saved total. Browser viewport override reset and only our created tab closed. Application, requirements, and existing test source were not edited. Server remains for its owner to stop. No unfinished deliverable work; outstanding probes are listed above.
