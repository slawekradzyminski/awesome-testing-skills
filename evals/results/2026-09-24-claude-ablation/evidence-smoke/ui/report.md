# Dispatch Desk — customer browser journey: release-readiness exploration

## Session summary
- **Scope:** The Alice-only browser journey: switching orders, editing delivery instructions (valid and `LOCKER:` rejection), choosing a service, keyboard use and focus, and desktop and narrow layouts, plus the API calls behind them. Excluded (per the brief): the admin APIs (refund and address), login, and hardening. Budget: 6 min and 80 browser actions. I used one browser session and one scripted `run-code` probe, about 45 interactions.
- **Environment:** 2026-09-24, http://127.0.0.1:51117, Playwright CLI session `ui-evidence-smoke` (Chromium, via the CLI's default), role alice (`X-Test-User` fixture header), viewports 1280×800 and 360×780 CSS px, no throttling. I read the source in `app/` directly. The git revision is unknown and the deployed build ID is unknown, so I can't confirm the source matches what's running (it behaved the same in every check).
- **Expected behavior:** `app/requirements.md`, "Browser experience" section (AC-1 to AC-5 below).
- **Result:** **No defects confirmed** within the checks I ran. The journey looks release-ready for the criteria below, with the gaps listed under "Residual risks".

### Acceptance criteria (taken from the ticket)
- AC-1: The selected order, the details shown and the target of a save stay consistent when lookups finish out of order.
- AC-2: Successful edits (instruction and service) survive a reload.
- AC-3: A rejected instruction shows feedback the user can act on, keeps the draft, never claims success, and leaves the stored note unchanged.
- AC-4: The service choices and instruction editing work with a keyboard, and focus is visible.
- AC-5: Desktop and narrow layouts are usable.

### Risk map
| Journey / risk | Evidence | Impact / priority | Experiment / observation | Status |
|---|---|---|---|---|
| A slow A100 lookup overwrites A200 | A100 lookups take 0.7 s (`app.py:60`). Code uses a `generation` token (`app.js` readOrder) | High: wrong order shown or saved | A200 → A100 → A200 within 100 ms. The A100 reply (#8) arrived after A200 (#7) and the UI stayed on A200 | Explored, no defect seen |
| Save reports success for the wrong order | save and setService capture `id`, then check `selected` | High | Code review only. The save and service buttons are disabled while a lookup is loading | Code checked; save during switch not run |
| LOCKER rejection shown as success | 422 branch in the save handler | Medium | 422, error text shown, draft kept, reload shows the earlier note | Explored, no defect seen |
| Keyboard access and focus | `:focus-visible` outline 3px #c65d00 | Medium | Tab order: note → save → express → standard. The outline showed on each. Enter and Space both activated buttons | Explored, no defect seen |
| Narrow layout hides controls | Media query at 600px | Low | At 360 px there is no horizontal overflow and all controls are visible | Explored, no defect seen |

## Check ledger
| Check | Criterion | Start state | Action → expected | Outcome | Evidence |
|---|---|---|---|---|---|
| C01 | baseline | `/`, alice, 1280×800 | Load → A100 details, controls enabled | passed | [C01](evidence/C01-initial-A100-desktop.png), HTTP #1 |
| C02 | AC-2 | A100 | Save "Ring twice QA" → "Delivery instruction saved"; still there after reload | passed | HTTP #2 (200), #3 (reload read) |
| C03 | AC-3 | A100 | Save "LOCKER: 12" → 422, error shown, draft kept; reload shows "Ring twice QA" | passed | [C03](evidence/C03-locker-rejected.png), HTTP #4 (422), #5 |
| C04 | AC-1 | A200 loaded | Pick A100, then A200 after 100 ms → UI shows A200 even though the A100 reply came last | passed | [C04](evidence/C04-race-after-A100-then-A200.png), HTTP #6–#8 |
| C05 | AC-2/AC-4 | A200 | Keyboard Enter on "Use express delivery" → 200, "Delivery service saved"; express still set after reload | passed | [C06](evidence/C06-keyboard-focus-express.png), HTTP #9, #10 |
| C06 | AC-4 | A200 | Tab sequence from the Order select: focus outline visible; Tab from the textarea → Save; Space saves | passed | `tabs` in [probe-output.json](evidence/probe-output.json), HTTP #11 |
| C07 | AC-5 | A200, 360×780 | Full-page screenshot → no overflow, controls visible | passed | [C07](evidence/C07-narrow-360.png) |
| C08 | AC-1 | A100 loading | Click Save while an order switch is in flight | not-run (time budget; code says the button is disabled during loading) | — |
| C09 | AC-3 | — | Blank or whitespace-only instruction, 400 path | not-run | — |
| C10 | AC-3 | — | Reject a service change (403/404) in the UI | not-run (no ordinary UI path; only the selected Alice order is sent) | — |

Visits (`evidence/visits.md` is folded in here): one route, `/` ("Dispatch Desk"), alice. States: A100 loaded (C01–C03), A200 after the race (C04), A200 express (C05–C06), narrow 360 px (C07).

Evidence notes: all five screenshots are in `evidence/`, and I opened C03 and C07 to confirm them. HTTP exchanges are in [evidence/http.jsonl](evidence/http.jsonl), numbered by `seq`. The only header was the fixture `X-Test-User`; no secrets appear. Response bodies are cut at 300 characters. The probe script is [evidence/probe.js](evidence/probe.js).

**Tool artifact (not a product bug):** in C06 the probe pressed Control+A on macOS. That didn't select the text, so the draft became "Leave at door QARing twice". The save itself behaved correctly.

## Findings
None confirmed. No code-evidenced defects either.

## Residual risks and coverage gaps
- Console errors were not collected. There was no performance timing beyond the intended 0.7 s delay. No screen reader was used, and I only checked the accessibility tree semantics in code (labels, `role=status`). No Safari or WebKit testing and no real devices.
- C08–C10 were not run. Next useful action: control timing with a route delay and try Save during a switch, and try a blank instruction.
- Feedback persists after a service change (it isn't cleared until the next load). That is a design observation, not a defect.

## Suggested regression scenarios
1. An out-of-order A100/A200 lookup leaves the UI and any save pointing at the last selected order, with no write to the other order.
2. A `LOCKER:` instruction gives 422, the draft is kept, no success text appears, and the stored note is unchanged after reload.
3. A keyboard-only service change and instruction save both persist after reload.

## Cleanup
Restored fixtures through the API: A100 note "Leave with reception", A200 note "Ring twice", A200 service "standard". None of these calls change the version counter (it stays 1), and I made no refunds or address changes. Browser session `ui-evidence-smoke` is closed. No mocks or routes are left.
