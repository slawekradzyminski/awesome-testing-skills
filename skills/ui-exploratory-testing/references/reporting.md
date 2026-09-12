# UI exploration report

Adapt this structure to the existing reporting system and size of the task. Keep one independently fixable problem per finding. A small session can hold findings inline; link existing bug records where appropriate.

## Session summary

- **Question and scope:** user outcome, screens/journeys, exclusions, and time/action limits.
- **Environment:** date, URL, deployed build, source revision and match/unknown, browser/version, role, viewport in CSS pixels, emulation/zoom, and relevant cache or throttling settings.
- **Expected behavior:** requirements/design basis and unresolved product questions.
- **Results:** consequential findings first, followed by explored states and material gaps.

| Journey / risk | Evidence or reason for concern | Impact and exploration priority | Experiment / observation | Status and next action |
| --- | --- | --- | --- | --- |

Useful statuses: explored with no defect observed, runtime-confirmed finding, code-evidenced finding (not reproduced), suspected, blocked, not explored. Keep untested risks distinct from confirmed bugs. Exploration priority and bug severity serve different purposes.

## Finding

**Title:** Journey or screen — observable problem

**Classification / evidence state:** functional, visual, accessibility, network, performance, or needs clarification; runtime-confirmed, code-evidenced, or suspected.

1. **Preconditions and reproduction:** role, data/form/session state, viewport if relevant, and the minimal sequence of actions. Record actual reproduction counts, including intermittent results.
2. **Actual result and evidence:** visible behavior, pertinent opened screenshot with a descriptive caption, DOM/accessible properties, sanitized requests/console messages, or measured timing as applicable. Distinguish captured evidence from evidence actually reviewed.
3. **Expected result and basis:** requirement/design/standard location or explicitly proposed expectation. Separate a design preference from a demonstrated user impairment.
4. **Impact:** affected users and task, demonstrated consequence, scope, workaround, and uncertainties. A hypothesized backend cause or possible downstream effect is not an observed fact.
5. **Severity:** apply the project's scale after assessing impact. If none exists, use High for demonstrated severe/core-flow impact, Medium for material impairment, Low for limited impact, or Unassessed when evidence is insufficient. Mark provisional assessments.
6. **Investigation:** relevant code locations/revision, alternative explanations checked, live versus injected conditions, and remaining questions. For source-only findings, explicitly leave browser reproduction and visual assessment pending.
7. **Retest and regression suggestion:** expected observable correction, neighboring state/viewport worth checking, and forbidden side effects to verify. Mark verified only after retesting the identified build.

## Evidence and closeout

Keep screenshots and other essential sanitized artifacts alongside the report or in the project's durable evidence location, with working relative links. Raw HAR files, storage state, traces, and console/network dumps can contain secrets; keep them local and excluded from commits unless reviewed and sanitized. Redact tokens, credentials, cookies, private data, and sensitive query parameters before sharing.

Summarize what was actually assessed across functional behavior, visuals, keyboard/accessibility, network, and performance. An unperformed category is not a pass. Record significant unexplored states, tool limits, prioritized residual risks, and cleanup of session-owned data, injected conditions, and browser sessions. Preserve meaningful findings even when the environment blocks further investigation.
