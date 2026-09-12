# Cart editor exploration

No confirmed discrepancy was found in the sampled journeys. This is a bounded result, not a defect-free certification.

## Charter and environment

Assess existing cart editing, provisional values, Save/Cancel side effects, totals and feedback against CART-1–4 and UI-1–2 in requirements.md. Runtime-only exploration; source was explicitly unavailable and was not requested again. No implementation, requirements, skills or existing tests were changed.

Runtime: http://127.0.0.1:49949. Session date: 2026-09-12; browser activity 09:16:02–09:17:58 UTC. Browser: headless Chromium 152.0.0.0 on macOS, dedicated cart04 session. CSS viewports 1280×720 and 375×812, default browser zoom; no throttling, mocks or device emulation. Source revision and deployed build identifier unknown. Only disposable Alice/Bob fixture data used. Stop condition: core scoped risks sampled or five minutes / 60 API requests / 45 browser actions reached.

## Observed checks

- **UI-1 provisional edit and Cancel — passed within stated scope.** Alice started at 1 / 12; entering 3 retained visible 1 / 12. Cancel displayed Edit cancelled and reopening showed 1. Bounded before/after network lists contained only the initial GET and no PUT. Evidence: [provisional-desktop.png](evidence/provisional-desktop.png), [after-cancel.png](evidence/after-cancel.png), [reopened-after-cancel.yml](evidence/reopened-after-cancel.yml), [network-before-cancel.txt](evidence/network-before-cancel.txt), [network-after-cancel.txt](evidence/network-after-cancel.txt).

- **UI-1 / CART-4 explicit Save and persistence — passed within stated scope.** Desktop Save of 4 returned PUT 200 followed by GET 200; UI acknowledged Cart updated and displayed 4 / 48. Independent API read confirmed totalItems 4 and totalPrice 48. New browser session reopened saved quantity 4. Evidence: [after-save.txt](evidence/after-save.txt), [network-after-save.txt](evidence/network-after-save.txt), [http.json](evidence/http.json), [reopened-saved-narrow.yml](evidence/reopened-saved-narrow.yml).

- **UI-2 narrow keyboard Save — passed within stated scope.** At 375×812, Tab, Tab, Enter opened Edit; ArrowDown changed 4 to 3; Tab, Enter saved. Visible total became 36 and Cart updated appeared. Independent API read confirmed 3 / 36. Evidence: [narrow-keyboard-saved.png](evidence/narrow-keyboard-saved.png), [keyboard-save.yml](evidence/keyboard-save.yml), [network-second-session.txt](evidence/network-second-session.txt), [cleanup.json](evidence/cleanup.json).

- **UI-2 visible invalid quantity feedback — passed within stated scope.** At 375×812, keyboard Save of 6 displayed native validation “Value must be less than or equal to 5.” No PUT occurred; saved quantity stayed 4. Evidence: [narrow-stock-error.png](evidence/narrow-stock-error.png), [network-after-error.txt](evidence/network-after-error.txt), [http.json](evidence/http.json).

- **CART-2 invalid input rejection — passed within stated scope.** All six API cases returned 400; GET after each returned Alice quantity 4 / total 48. Evidence: [http.json](evidence/http.json).

- **CART-3 overstock and stock stability — passed within stated scope.** API quantity 6 returned 409, subsequent cart remained 4 / 48; final products read showed stockQuantity 5. Evidence: [http.json](evidence/http.json), [cleanup.json](evidence/cleanup.json).

- **CART-1 sampled identity isolation — passed within stated scope.** Bob remained quantity 2 / total 24 after Alice edits and cleanup. Anonymous GET returned 401. Full ownership/security assessment not performed. Evidence: [http.json](evidence/http.json), [cleanup.json](evidence/cleanup.json).

## Visual inspection and important qualifications

All four supplied PNGs were actually opened and inspected. At desktop width the provisional input, separate saved totals, Save and Cancel were legible and contained within the card. The cancelled state displayed “Edit cancelled”. At narrow width the card and text fit the viewport; the native stock validation popup was visible, and the successful keyboard Save displayed 3 / 36 with “Cart updated”. This sampling does not establish accessibility conformance.

The narrow overstock attempt was client validation, not a server error. After validation returned focus to the quantity field, the next Tab/Enter tried Save again; it did **not** exercise Cancel. This is an exploration targeting correction, not a reported product bug. The preserved snapshot is named narrow-second-invalid-attempt.txt. A fresh browser was then used for a successful keyboard-only edit and Save. The first session console had zero messages; the second session console was not separately inspected. No performance SLA was assessed.

Cancel was observed once with valid provisional quantity 3. The network list immediately before and after Cancel contained the same initial GET and no mutation. A subsequent Edit showed the saved value 1. The later independent API read verified Save persistence, not a dedicated immediate Cancel read.

## Prioritized residual risk map

| Journey / state | Evidence and uncertainty | Priority / next experiment |
| --- | --- | --- |
| Role switch while editing or saving | Only Alice UI journey and Bob API reads exercised; transition timing remains untested. | medium: Switch account with a provisional edit and a deliberately delayed save; verify displayed owner and persisted carts. |
| Server failure feedback and recovery | UI overstock was blocked by browser validation, so no UI server-error response was exercised. | medium: Trigger an authorized controlled server error and verify visible message, retained edit, and successful retry. |
| Zero removal and exact stock boundary | Zero would remove the item without an implemented add-back route; zero and exact five were not exercised. | medium: Use a separately resettable fixture to test zero removal and quantity five. |
| Keyboard Cancel and broader accessibility | Desktop Cancel used pointer; invalid narrow Save refocused input, so the subsequent Tab/Enter activated Save again. No keyboard Cancel success claim. | low: Test keyboard Cancel with valid and invalid provisional values, then desktop keyboard journey and screen-reader announcements. |

## Limitations and useful follow-up

- Source unavailable by session constraint; source revision, deployed build identifier and source/build match unknown. No source or test review.
- No full authorization assessment, anonymous writes, Bob UI edits, racing requests, server-error UI recovery, removal, or exact-stock boundary.
- Visual samples: desktop 1280×720 and narrow 375×812 in headless Chromium 152; no real mobile, other browser, intermediate viewport or screen reader.
- Native number-field validation prevented an overstock update through UI; API 409 was verified separately.
- Cancel persistence evidence is bounded network absence plus reopened value; independent API read was taken after the later explicit Save, not directly after Cancel.
- One run-code observation failed due to tool callback signature; it made no application request. A second run-code observation produced no usable output; eval supplied browser metadata.

If source is available in a later session, the relevant frontend edit/submit handlers and backend validation, ownership and persistence routes, together with deployed revision identification, would allow comparison of hidden branches with these observed outcomes. No claim is made that source access would necessarily reveal defects.

Valuable regression scenarios: Cancel a valid edit with **zero PUTs** and unchanged persisted cart; Save by keyboard then reload and verify quantity/total; reject each invalid API quantity without mutation; switch identities during an edit and verify ownership; recover from a controlled server error. Regression implementation is outside this exploration.

## Accounting and cleanup

42 browser commands including observations, screenshots, two closes and a failed tool observation; 28 API requests (6 browser + 22 direct), plus 6 document/static requests, for 34 observed HTTP requests. Limits were 45 browser actions and 60 API requests. No availability failures. See [accounting](evidence/accounting.txt) and the two browser network lists. The malformed run-code callback was a tool error and caused no application request.

Alice restored to quantity 1 / total 12 and independently read back; Bob unchanged at 2 / 24; stock remains 5. Both session-owned browser instances closed. No mocks, source changes, service lifecycle changes, or remaining data mutations.

Unfinished checks are listed in the residual risk map; no application repair or source fix was authorized or attempted. All deliverables are local to this candidate directory.
