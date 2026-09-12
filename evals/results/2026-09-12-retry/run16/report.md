# Public login exploration

No confirmed product defect was found in this bounded read-only pass. This is limited positive evidence for public desktop navigation, not a full login certification.

## Runtime observations

- Login rendered a labelled Username and Password form, a training-environment notice, and public navigation. Desktop screenshot: [login](evidence/login.png). The screenshot was opened and visually inspected.
- Keyboard Tab first focused the logo; after three further Tab presses focus reached Username. This checks one short traversal only: [focus evidence](evidence/login-keyboard.txt).
- Forgot password opened `/forgot-password`; Back to login returned to `/login`. The recovery page exposed a labelled identifier input and reset action; no reset was submitted. [Recovery screenshot](evidence/forgot.png), opened and inspected.
- In-card Register opened `/register`, matching the snapshot E2E test expectation. Its Sign in navigation button returned to `/login`. [Registration screenshot](evidence/register.png), opened and inspected; [return evidence](evidence/register-return-login.txt).
- The three inspected desktop screenshots had legible content and no obvious overlapping form controls. Recovery content extends vertically; that alone is not a defect. No responsive claim is made.
- Footer links identify the blog, LinkedIn, and coffee support destinations. Destinations were not visited.
- Four unauthenticated direct GETs—`/login`, `/v3/api-docs`, `/api/v1/products`, `/api/v1/cart`—each returned HTTP 403 with `Server: cloudflare` and `error code: 1010`. These are edge observations, not confirmed backend authorization failures. Browser login remained accessible. [Full HTTP evidence](evidence/http.json) and individual response bodies are retained.

## Expectations and source distinction

No numbered product requirement was supplied. Source tests document registration navigation to `/register`, and submitted login validation/authentication cases. Source login code uses associated labels, password input type and submission-time validation. The backend snapshot permits API docs and requires authentication for other unlisted endpoints. None of this establishes the deployed revision. [Focused source notes](evidence/source-contracts.txt) identify the exact files read. Tests were not executed because they submit forms and create accounts.

## Important authorized-session gaps

- **High: Authentication and session lifecycle** — Read-only constraints exclude the source-defined success/failure and MFA flows. Next: In an authorized disposable session, verify valid/invalid login, MFA challenge, return navigation, logout and token expiry with throwaway accounts.
- **High: Password recovery safety and delivery** — Recovery UI promises neutral responses and mentions local developer-token output; neither response behavior nor token exposure was exercised. This is a coverage gap, not evidence of leakage. Next: Use an authorized disposable mailbox/account to verify neutral known/unknown identifier responses, token expiry/single-use and absence of developer tokens in deployed responses.
- **Medium: API access contract** — Cloudflare 403/1010 prevented reaching the API behavior described by the snapshot. Next: With an authorized origin-reaching disposable setup, verify public API-docs access and unauthenticated products/cart rejection without exposing private records.
- **Medium: Validation and accessibility** — Submission-time errors and mobile layout were not exercised. Next: In a disposable authorized session, test empty/min/max inputs, error association/announcement and keyboard focus at mobile widths.

## Budget, limitations and cleanup

4 of 12 permitted direct HTTP requests; 22 of 30 browser API operations including snapshots and cleanup. No retries, form submissions, credential access or intentional mutations. See [action ledger](evidence/browser-actions.txt).

- PUBLIC READ-ONLY: no login/reset/registration submissions, emails, authenticated browsing, MFA, rate-limit or account enumeration tests.
- All four direct GETs were blocked with Cloudflare 403 and body error code: 1010; no origin API status or contract could be confirmed.
- Source snapshots are not verified deployed revisions; source tests were read but not executed.
- Dedicated newly created browser session/tab used; clean underlying profile storage isolation was not independently verified. No stored credentials were accessed.
- Desktop screenshots only; narrow viewport, zoom, complete focus sequence, screen-reader error announcement, and network tracing were not tested.
- External footer destination URLs were inspected but not visited because they are outside the assigned runtime.
- Exact elapsed duration and token usage were not instrumented; approximately three minutes elapsed by operator estimate, below the five-minute budget.

Finished evidence authoring at 2026-09-12T08:50:24.565872+00:00. Closed the test tab; no server/source changes. Only report, evidence and submission files were created.
