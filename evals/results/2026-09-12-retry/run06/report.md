# Cart exploration report

Confirmed one high-priority discrepancy: **UI-1 — Cancel saves the edited quantity**. Desktop pointer and narrow keyboard reproductions both changed persisted Alice cart state. This can silently retain an edit the user intended to discard.

## Reproduction and evidence

1. Alice starts at quantity 1, total 12.
2. Open Edit quantity, enter 3, click Cancel.
3. The editor closes and shows quantity 3, total 36 and “Cart updated”. An independent API GET confirms the saved quantity is 3. Reopening Edit also shows 3.
4. After restoring 1, repeat at 375×667 using Tab, Tab, Return to activate Cancel with draft 2. The UI and independent GET show persisted quantity 2, total 24.

Expected: discard the draft, retain quantity 1 and total 12, and reopen with 1.

Evidence: [reproduction](evidence/reproduction.txt), [HTTP responses](evidence/http.json), [desktop screenshot](evidence/cancel.png), [narrow screenshot](evidence/narrow-cancel.png). Both screenshots were opened and visually inspected. Persistence is directly confirmed; the specific browser update request was not captured.

## Checks that passed

- Alice/Bob baselines were isolated; Alice changes left Bob at 2/24. Anonymous cart GET returned 401.
- Save 4 displayed 4/48 and success feedback; reopening showed 4.
- API negative, fractional, missing, null, string, and boolean quantities returned 400. Every rejection was followed by a GET confirming unchanged 4/48.
- Quantity 6 returned 409 through the API; UI Save 6 displayed native maximum validation. Persisted cart remained 4/48.
- Keyboard Save restored 1/12. Narrow Cancel was reachable by keyboard (functional defect above). The inspected narrow result fitted the viewport with visible feedback.
- Product stock remained 5 after edits.

## Remaining risks and limitations

Zero/removal and empty-cart behavior remain untested because removal cannot be reversed through the supported feature. Next use a resettable fixture. Identity switching with drafts and delayed/failed or repeated Save operations warrant follow-up. Bob writes, anonymous PUT, and comprehensive accessibility were not covered. No source was available or inspected. No defects are inferred from these gaps.

## Cleanup and budget

Alice restored to quantity 1 / total 12; Bob verified unchanged at 2 / 24; stock verified 5. Test-created browser tab closed and viewport reset.

26 direct API requests are recorded. Browser interaction count: 21 (including tab creation, viewport set/reset and close; excluding read-only observations and browser selection). Browser-generated API requests were not instrumented, so no exact combined count is claimed. Approximately 169 seconds elapsed from the API baseline timestamp to report creation, plus initial requirement reading/browser setup; the exploration used the five-minute timebox. Token/credit usage was not available.
