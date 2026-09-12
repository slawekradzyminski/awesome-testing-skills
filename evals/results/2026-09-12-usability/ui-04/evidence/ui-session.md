# Browser observation log

Runtime: http://127.0.0.1:49526/. Chrome via available browser agent. Source and deployed revision unknown. Desktop screenshot 1728×907 pixels; narrow viewport explicitly 375×812 CSS pixels. No throttling or mocked responses were introduced. Exact desktop CSS dimensions/browser version were not collected.

1. Opened dedicated cart tab. Alice selected; Workshop notebook, price 12, stock 5, quantity 1, total 12.
2. Clicked Edit quantity. Focus moved to quantity input, saved value 1.
3. Entered draft 3. Summary remained quantity 1 / total 12.
4. Clicked Cancel. Editor closed, text “Edit cancelled”, summary 1 / 12, focus returned to Edit quantity. Captured and visually opened `cancel.png`. Direct GET independently returned Alice quantity 1, totalPrice 12.
5. Pressed Return on focused Edit quantity. Reopened value was 1. Up, Up, Tab produced draft 3 and focused Save. Return saved. Editor closed; summary quantity 3 / total 36 and “Cart updated”. Captured and visually opened `save.png`. Direct GET independently returned Alice 3 / 36; Bob remained 2 / 24.
6. Set viewport to 375×812 and reloaded. Alice remained 3 / 36. Tab, Tab, Return opened Edit and focused quantity; saved value 3.
7. Entered 6, Tab, Return on Save. Browser validation read “Value must be less than or equal to 5.” Draft remained 6; summary stayed 3 / 36. Captured and visually opened `narrow-error.png`; form fit viewport, validation bubble partly overlaying buttons while displayed.
8. Tab, Tab, Return reached Cancel and closed editor despite invalid input. “Edit cancelled”; summary still 3 / 36. Direct GET confirmed 3 / 36. No browser network log was available, so this does not prove the absence of an update request.
9. Return reopened editor at saved 3. Down, Down, Tab, Return saved 1. Summary 1 / 12 and “Cart updated”. Captured and visually opened `narrow-restored.png`; card, totals, and feedback fit the narrow viewport without visible clipping.
10. Reset temporary viewport override and closed the session-owned tab. Final direct GETs confirmed Alice 1 / 12 and Bob 2 / 24.

# Accounting
27 state-changing browser operations: 1 create/navigation, 2 clicks, 2 quantity setValue operations, 18 key presses, 1 reload, 1 viewport set, 1 viewport reset, 1 close. Also 12 explicit accessibility snapshots and 4 screenshot captures, each opened inline; 43 combined interaction/observation operations. Browser selection and capability documentation were setup reads.
23 direct HTTP API requests, fully recorded in http.json. Browser-generated API requests were not instrumented and their exact count is unknown. No retry loops, no availability failures, no source reads, and no service lifecycle changes. Browser work was deliberately small (two page loads, two successful Save submissions, one invalid Save attempt) to leave substantial room under the API budget, but an exact combined request total cannot be certified.
