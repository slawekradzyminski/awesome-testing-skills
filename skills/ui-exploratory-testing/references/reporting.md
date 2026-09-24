# UI exploration report

Adapt this structure to the existing reporting system and size of the task. Keep one independently fixable problem per finding. A small session can hold findings inline; link existing bug records where appropriate.

## Session summary

- **Question and scope:** user outcome, screens/journeys, exclusions, and time/action limits.
- **Ticket and criteria:** ticket ID/link or supplied text, acceptance criteria used, and which interpretations await confirmation.
- **Environment:** date, URL, deployed build, source revision and match/unknown, browser/version, role, viewport in CSS pixels, emulation/zoom, and relevant cache or throttling settings.
- **Expected behavior:** requirements/design basis and unresolved product questions.
- **Results:** consequential findings first, followed by explored states and material gaps.

| Journey / risk | Evidence or reason for concern | Impact and exploration priority | Experiment / observation | Status and next action |
| --- | --- | --- | --- | --- |

Useful statuses: explored with no defect observed, runtime-confirmed finding, code-evidenced finding (not reproduced), suspected, blocked, not explored. Keep untested risks distinct from confirmed bugs. Exploration priority and bug severity serve different purposes.

For several findings, add a compact index after triage: ID, title/link, type, severity, evidence state, and status. Reuse project IDs and labels; otherwise use stable session-local IDs such as UI-01. Keep IDs stable when severity changes. Separate confirmed defects, unresolved questions and improvement suggestions in the summary; do not count all entries as confirmed bugs.

## Evidence package and checked criteria

In the report or `evidence/checks.md`, list every agreed ticket criterion and the important exploratory checks beyond it. Label a proposed criterion until the user confirms it. Link each check to what was actually observed:

| Check | Ticket criterion / risk | Page and starting state | Action and expected result | Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| C01 | AC-1 or exploratory risk | route, role, viewport | Short observable contrast | passed / failed / blocked / not-run | screenshot and HTTP IDs |

Keep a concise visit log in the report or `evidence/visits.md`: sanitized URL/route, page title, role, viewport, significant state, visit order, and linked check IDs. Group repeat visits unless their changed state matters. Capture a representative screenshot of each distinct in-scope page or significant state that the browser tool can show, plus before/after images for visual or state-transition findings. Name files by check/state, open decisive images to confirm they show the intended evidence, and link them from the ledger. Record a capture limitation instead of inventing a screenshot.

Preserve relevant browser HTTP exchanges in `evidence/http.jsonl`, or linked Markdown entries when export is unavailable. Correlate each with the action/check ID and record sequence/time, method and sanitized URL, pertinent request headers/body, response status and pertinent headers/body, and any follow-up read that establishes persisted state. Include failed calls and a representative passing contrast. Summarize repetitive requests and static assets; a raw HAR or unreviewed network dump is not the report. Mark redactions and truncation, and keep tokens, cookies, passwords and private data out of the evidence package.

## Classify findings for triage

Use the project's taxonomy when available. Otherwise choose a primary type and add secondary labels only when useful:

| Type | Evidence needed |
| --- | --- |
| FUI — functional UI | An ordinary interaction produces an outcome that violates an established rule, including unintended writes or misleading runtime feedback |
| VIS — visual | An inspected visual state and a concrete effect on readability, content or operation |
| A11Y — accessibility | A reproducible barrier for an affected interaction mode, with the relevant keyboard sequence, accessible properties or measurements |
| UX — user experience | A concrete obstacle to understanding or completing a task; label a proposed design preference as a suggestion when no requirement or impairment is established |
| NET — network/integration | A request/response or missing/duplicate interaction linked to an observable user or system consequence |
| PERF — performance | Timing samples and conditions tied to an agreed expectation or demonstrated task impairment |
| D — documentation | A specific help page, instruction or example conflicts with established intended behavior; retain its location/version and the conflicting evidence |

Use one finding with related labels when the same independently fixable problem affects several categories. A console error, failed request or scan warning is an observation to investigate, not automatically another bug. Misleading text in a live form can be FUI or UX; documentation-only findings concern the supporting documentation. Honor the user's category exclusions and do not expand a focused journey into a full audit.

Severity describes impact, while repair priority also depends on release and business context. Assess consequences for the affected users: a core task blocked for keyboard users can have high severity even if mouse users can complete it. Do not assign a fixed severity to every accessibility or documentation finding. Explain priority separately if requested; leave it unassessed when the needed context is missing.

## Finding

**Title:** [type] Journey or screen — observable problem

**ID:** existing issue ID or stable session-local ID.

**Type:** project category or FUI / VIS / A11Y / UX / NET / PERF / D.

**Status:** Open / Needs clarification / Fixed, awaiting retest / Verified.

**Evidence state:** runtime-confirmed / code-evidenced (not reproduced) / document-evidenced / suspected.

**Observed on:** date; refer to session environment and note any finding-specific differences.

1. **Preconditions and reproduction:** role, data/form/session state, viewport if relevant, and the minimal sequence of actions. Record actual reproduction counts, including intermittent results.
2. **Actual result and evidence:** visible behavior, pertinent opened screenshot with a descriptive caption, DOM/accessible properties, sanitized requests/console messages, or measured timing as applicable. Distinguish captured evidence from evidence actually reviewed.
3. **Expected result and basis:** requirement/design/standard location or explicitly proposed expectation. Separate a design preference from a demonstrated user impairment. For a standards claim, verify the applicable criterion/version and explain how the evidence meets it; do not guess criterion numbers. For documentation, identify the exact conflicting instruction and proposed correction, leaving unresolved intent as a question.
4. **Impact:** affected users and task, demonstrated consequence, scope, workaround, and uncertainties. A hypothesized backend cause or possible downstream effect is not an observed fact.
5. **Severity:** apply the project's scale after assessing impact. If none exists, use High for demonstrated severe/core-flow impact, Medium for material impairment, Low for limited impact, or Unassessed when evidence is insufficient. A rejected edit shown as saved, with unchanged persisted data and no demonstrated downstream harm, usually supports Medium; justify High with evidence of a more severe consequence. Mark provisional assessments.
6. **Investigation:** relevant code locations/revision, alternative explanations checked, live versus injected conditions, and remaining questions. For source-only findings, explicitly leave browser reproduction and visual assessment pending.
7. **Acceptance criteria, retest and regression suggestion:** expected observable correction, neighboring state/viewport or interaction mode worth checking, and forbidden side effects to verify. Record retested build/date and evidence only after retesting. Identify useful automated coverage and any manual keyboard, visual or assistive-technology verification still needed.

This is a reusable finding template for the session report or a draft ticket. If separate files are useful, an optional name is `[severity][type] UI-01 - Short description.md`; use the project's convention when one exists. Assess impact before adding the severity label. Preparing a ticket does not authorize posting it to an external tracker.

Count independent reproductions only when each attempt has a known starting state and its own observed result. If several actions precede one screenshot or state read, describe the sequence as one observation rather than claiming each action was confirmed separately.

## Evidence and closeout

Keep screenshots and other essential sanitized artifacts alongside the report or in the project's durable evidence location, with working relative links. Raw HAR files, storage state, traces, and console/network dumps can contain secrets; keep them local and excluded from commits unless reviewed and sanitized. Redact tokens, credentials, cookies, private data, and sensitive query parameters before sharing.

Summarize what was actually assessed across the in-scope categories: functional behavior, visuals, keyboard/accessibility, UX, network, performance and documentation. An unperformed category is not a pass. Record significant unexplored states, tool limits, prioritized residual risks, and cleanup of session-owned data, injected conditions, and browser sessions. Preserve meaningful findings even when the environment blocks further investigation.

When source was unavailable, include a short handoff explaining what the runtime checks established, which relevant source/revision could improve the assessment, and what it would help inspect. Make the benefit concrete, such as hidden validation branches, ownership checks or persistence logic. Do not promise more bugs or repeat a request the user has already declined; this is context for a possible later session.
