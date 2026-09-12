# Public login exploration

No consequential product defect was confirmed. This was a bounded, public, read-only pass; it does not establish that authentication or recovery works.

## Session and charter
Explore whether a visitor can understand the login form, reach recovery and registration, and use the public interface at desktop and narrow widths. Stop at five minutes or 30 browser actions; do not submit, authenticate, trigger SSO, create records, send email, or use stored credentials.

Run date: 2026-09-12. Runtime: https://awesome.byst.re. Fresh session `retry14`, HeadlessChrome 152.0.0.0 on macOS; viewports 1440×900 and 375×812 CSS pixels. Default browser network/cache behavior; no emulation beyond viewport resize, throttling, mocks, or fault injection. Browser live window approximately 08:43:25–08:44:54 UTC (89 seconds); whole task approximately four minutes including source reading and reporting, not precisely instrumented. Four direct HTTP GETs. Twenty-two browser command invocations, or 29 conservatively counting the successful script's four Tab presses and four DOM reads separately. One earlier script failed parsing before executing. No unavailable token/usage metrics claimed.

The supplied frontend package version is 3.7.14. Git revision IDs were not present in the inspected snapshot directories; attempts to resolve them failed. Exact deployed revision is unknown. Observed deployed main asset is `index-D3mvI_4r.js`; branding query version `3.6.13` is not proof of deployed application revision. Relevant source fingerprints are saved in [source-fingerprints.json](evidence/source-fingerprints.json). Source/runtime correspondence is unverified.

## Expectations and evolving risk map
No separately numbered requirement was supplied. Source and inspected tests are implementation evidence rather than independent product requirements. Public navigation labels imply their destinations should be reachable; legibility and associated input labels are inferred usability expectations.

| Journey / risk | Evidence and plausible failure | Priority / experiment | Result / next step |
| --- | --- | --- | --- |
| Login fields and submit | `loginPage.tsx` uses `noValidate`, on-submit Zod resolver; missing native constraints could otherwise be mistaken for no validation | High: inspect semantics without submitting | Username/password have associated labels and password type. Native required and autocomplete absent. Source validates length 4–255; error execution remains blocked by scope |
| Login → recovery → login | Forgot control explicitly has type button and navigates; accidental submission would be consequential | Medium: ordinary clicks, observe page and requests | Both destinations reached; no mutation requests in captured browser window |
| Login → registration | Public Register link should reach account creation UI without creating an account | Medium: click nav Register | Registration fields and button rendered; no submission |
| Narrow layout | Large hero and auth cards could obscure controls | Medium: compare desktop/narrow and lower page position | No horizontal overflow measured at 375 px; form and footer are reachable. Sign in lies below initial narrow fold, which is not by itself a defect |
| Public API boundary | Security config permits docs and requires auth for other endpoints | High: GET only approved docs/products/cart plus login control | All Python requests returned edge-style 403, including public login; backend authorization not established |
| Keyboard focus | Inspected `a11y.auth.spec.ts` expects predictable tab order, including conditionally visible SSO | Medium: four ordinary Tab presses | Script executed; console output was not captured, so actual focus sequence cannot be asserted. Test suite inspected, not run |

## Reviewed evidence

- [Desktop login](evidence/login-desktop.png): opened and inspected. Clear field labels, submit and recovery controls, readable notice, intact footer.
- [Initial narrow login](evidence/login-mobile.png): opened and inspected. Stacked hero/form; no visible clipping. [Narrow lower page](evidence/mobile-focused.png): opened and inspected; form submit, Register, and footer accessible in the scrolled viewport. Filename does not establish focus; screenshot followed a failed focus script.
- [Narrow registration](evidence/register-mobile.png): opened and inspected. Username, email, password, first/last names and account button visible at the inherited scroll position. This is not evidence of registration success.
- [Login semantics](evidence/login-dom.txt), [narrow measurements](evidence/mobile-dom.txt), [recovery snapshot](evidence/forgot-password.yml), [returned login](evidence/login-return.txt), [registration snapshot](evidence/register.txt).
- [Browser requests](evidence/browser-requests.txt): 14 observed GETs, all 200, including login and public assets. No mutations appear in this bounded captured window; this is not a global side-effect guarantee.
- [Console](evidence/console.txt): zero errors/warnings; three verbose browser suggestions concerning autocomplete. No demonstrated password-manager failure; absence of autocomplete remains a low-priority follow-up, not a confirmed product defect.
- [HTTP results](evidence/http.json): four GETs, each 403. Product/cart responses contain `error code: 1010`. Browser login 200 is a contrasting control that makes direct-client/edge filtering plausible; no claim about its exact cause. No retries or bypass attempts were made.

## Residual risks and useful authorized follow-up

High priority: with explicit permission and a disposable account, verify successful/failed login, server error feedback, session return destinations, logout, and MFA. Check duplicate-submit prevention and forbidden requests during loading. Recovery needs authorization to submit and inspect delivery/token behavior; registration needs authorized disposable data. These were deliberately untouched.

Medium priority: obtain a known deployed revision and authorized client for product/cart access-boundary checks; do not interpret edge rejection as application authorization. Repeat full keyboard path with captured active elements, including validation errors, and assess screen-reader announcements. SSO buttons were absent at runtime; source conditionally renders them, so absence is not a bug. No SSO provider flow was invoked.

Low priority: check intended password-manager support and add explicit autocomplete semantics if required. Test real mobile browser/keyboard and another desktop engine; viewport resizing is not real-device coverage. External footer destinations were inspected as links but not visited because they are outside the assigned runtime.

Potential regression scenarios: public recovery round-trip without any mutation request; public registration navigation; readable login controls at 375 px with no horizontal overflow; approved disposable-session validation and authentication with accurate errors and stable post-login state. No tests were changed or executed.

## Cleanup
Closed only the fresh `retry14` browser session. No credentials, forms, records, emails, source changes, mocks, or external issues were created. Local CLI snapshots/logs and sanitized report evidence remain in this candidate directory. No server process was stopped.
