# API exploration report

Adapt this structure to the existing reporting system and size of the task. Keep one independently fixable problem per finding. A small session can contain its findings inline; link existing bug records when appropriate.

## Session summary

- **Question and scope:** requested operations/workflow, exclusions, time/request limits.
- **Ticket and criteria:** ticket ID/link or supplied text, acceptance criteria used, and which interpretations await confirmation.
- **Environment:** date, base URL, configuration, test roles, source revision, deployed build, and whether they match (or unknown).
- **Expected behavior:** requirement/contract version and unresolved product questions.
- **Results:** consequential findings first, followed by explored behavior and material gaps.

| Area / risk | Evidence or reason for concern | Impact and exploration priority | Probe / observation | Status and next action |
| --- | --- | --- | --- | --- |

Useful statuses: explored with no defect observed, runtime-confirmed finding, code-evidenced finding (not reproduced), suspected, blocked, not explored. Keep untested risks distinct from confirmed bugs. Exploration priority and bug severity serve different purposes.

For several findings, add a compact index after triage: ID, title/link, type, severity, evidence state, and status. Reuse project IDs and labels; otherwise use stable session-local IDs such as API-01. Keep IDs stable when severity changes. Separate confirmed defects, unresolved questions and improvement suggestions in the summary; do not count all entries as confirmed bugs.

## Evidence package and checked criteria

Keep a check ledger in the report or `evidence/checks.md`. Include every agreed ticket criterion and the important exploratory checks chosen beyond it. Record the source of the expected result; label a proposed criterion until the user confirms it. Use a compact table:

| Check | Ticket criterion / risk | Operation and starting state | Expected / observed | Outcome | HTTP evidence |
| --- | --- | --- | --- | --- | --- |
| C01 | AC-1 or exploratory risk | `POST /api/...`, role, state | Short contrast | passed / failed / blocked / not-run | `http.jsonl` entry ID |

Preserve sanitized HTTP exchanges for meaningful probes in `evidence/http.jsonl`, or linked Markdown entries when structured export is unavailable. Each entry needs its check ID, sequence/time, role, method and path, relevant request headers/body, response status and relevant headers/body, plus a follow-up read when the claim concerns persisted state. Record redactions and truncation; do not silently present a shortened response as complete. Capture failed checks and a representative passing contrast, while summarizing repetitive equivalent probes instead of dumping every request. The report should stand on its own if a temporary runtime or tool trace disappears. Never store authorization tokens, cookies, passwords or private customer data in the evidence package.

## Classify findings for triage

Use the project's taxonomy when available. Otherwise choose a primary type:

| Type | Use when |
| --- | --- |
| FA — functional API | Runtime behavior violates an established business rule or interface contract, including validation, authorization or persistence failures |
| D — documentation | A specific document, schema or example is inaccurate or incomplete relative to the established intended behavior |
| PERF — performance | Recorded measurements demonstrate an agreed performance expectation being missed or a concrete client/workflow impairment |

Add secondary labels, such as security or developer experience, where supported by evidence. A documentation/runtime mismatch alone does not determine which side is wrong: retain the conflicting declarations and mark the decision unresolved when the intended contract is unknown. Misleading runtime validation feedback is application behavior, even if its symptom is text. Honor exclusions such as a functional-only investigation; this taxonomy does not require a documentation audit.

Severity describes demonstrated impact; repair priority additionally depends on release and business context. Do not derive severity from a type label or HTTP status alone. If priority is requested, explain it separately or leave it unassessed when that context is missing.

## Finding

**Title:** [type] METHOD /path — observable problem

**ID:** existing issue ID or stable session-local ID.

**Type:** project category or FA / D / PERF.

**Status:** Open / Needs clarification / Fixed, awaiting retest / Verified.

**Evidence state:** runtime-confirmed / code-evidenced (not reproduced) / document-evidenced / suspected.

**Observed on:** date; refer to session environment and note any finding-specific differences.

1. **Preconditions and reproduction:** role, test data state, minimal steps and sanitized request. Describe placeholders so another tester can substitute their own credentials safely.
2. **Actual result:** status, pertinent headers/body, resulting state, and actual reproduction count. Include essential evidence inline and link larger sanitized artifacts.
3. **Expected result and basis:** requirement or contract location; explicitly label a proposed expectation if intent is unresolved. For documentation mismatches, name the exact operation/schema/property and conflicting declaration.
4. **Impact:** affected user/workflow, demonstrated consequence, scope, workaround, and uncertainty. Do not present hypothetical exploitation or downstream failure as observed fact.
5. **Severity:** apply the project's scale after assessing impact. If none exists, use High for demonstrated severe/core-flow impact, Medium for material impairment, Low for limited impact, or Unassessed when evidence is insufficient. A rejected edit reported as saved, with unchanged persisted data and no demonstrated downstream harm, usually supports Medium; justify High with evidence of a more severe consequence. Mark provisional assessments.
6. **Investigation:** source file/line and revision, likely cause clearly labeled, alternative explanations checked, and unresolved questions. For source-only findings, distinguish the defect's code evidence from unverified runtime reachability.
7. **Acceptance criteria, retest and regression suggestion:** the required observable correction, neighboring behavior worth checking, and the lowest useful test level. Record retested build/date and evidence only after retesting. A proposed fix is not a verified fix. For a documentation finding, identify the exact declaration and proposed correction, then check it against the agreed contract and relevant runtime evidence.

This is a reusable finding template for the session report or a draft ticket. If separate files are useful, an optional name is `[severity][type] API-01 - Short description.md`; use the project's convention when one exists. Assess impact before adding the severity label. Preparing a ticket does not authorize posting it to an external tracker.

Count attempts as independent reproductions only when each has its own starting state, triggering action and follow-up observation. Two writes followed by one read establish one observed outcome. If a disposable ledger simulates a payment, report the demonstrated ledger state; do not claim an actual payout or financial loss without evidence of that effect.

## Closeout

Record tested and untested behaviors, residual risks in priority order, environment/tool limitations, and cleanup performed or still needed. State whether relevant existing tests were inspected, executed, failed, or unavailable. Mark a finding verified only after retesting the identified build. Keep raw secrets, tokens, cookies, private data, and unreviewed captures out of shared reports.

When source was unavailable, include a short handoff explaining what the runtime checks established, which relevant source/revision could improve the assessment, and what it would help inspect. Make the benefit concrete, such as hidden validation branches, ownership checks or persistence logic. Do not promise more bugs or repeat a request the user has already declined; this is context for a possible later session.
