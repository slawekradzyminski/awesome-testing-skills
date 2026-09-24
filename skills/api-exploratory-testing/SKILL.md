---
name: api-exploratory-testing
description: Explore APIs through focused source-code analysis and live HTTP experiments, identify risky behavior, and report reproducible bugs and contract gaps. Use for exploratory API testing and code-informed bug hunting; regression-suite implementation is a separate task.
---

# API Exploratory Testing

Investigate how an API can fail its users. Combine implementation analysis with experiments against the running system, following evidence and new questions rather than exhausting a checklist. Deliver actionable findings, a prioritized risk assessment, and an honest account of what was explored.

**Session deliverable:** unless the project sets another location, create `report.md` and `evidence/` early. Keep a passed/failed/blocked/not-run check ledger tied to ticket criteria, plus sanitized request/response entries with sequence, method/path, role, status and a follow-up read for persisted-state claims. Save evidence during probes; do not defer the exchange log to closeout. If capture is unavailable, mark the affected check blocked or partially evidenced. Use [the report guide](references/reporting.md) for the complete format and redaction rules.

## Establish the target and invite source access

Start from the user's request, existing conversation, and applicable repository instructions. If application source has not been supplied or located, encourage the user to provide the backend repository/path and branch or revision, plus related services where relevant. Explain that source access helps identify hidden branches, authorization boundaries, and failure paths that API documentation alone may miss. Prefer access to the relevant code over asking for a whole repository dump; never request secrets in chat.

Also establish the API base URL, intended behavior or contract, feature scope, available test roles, and permissible data changes. Reuse information already available; ask only for missing details that affect the next step. Locate source through provided project links/configuration without searching unrelated private projects. Do not repeatedly ask for code if the user cannot share it.

If there is a ticket or story, extract its acceptance criteria and turn them into observable API outcomes, including relevant error and state-preservation cases. If no ticket or criteria are available, invite the user once to share them or name the two or three outcomes that matter most; offer concrete candidate outcomes inferred from the feature. In an interactive session, ask this before the first experiment while continuing independent work. In a one-shot session that cannot receive a reply, put two or three proposed outcomes in the report, mark them unconfirmed, and proceed. When a material rule is ambiguous, present your best proposed interpretation in one concise question for confirmation. Continue checks that do not depend on an answer, label proposed criteria as unconfirmed, and link agreed criteria to check results in the report. Do not make the user fill in a generic questionnaire when the ticket and code already answer it.

- **Source and runtime available:** perform code-informed exploration and live HTTP verification.
- **Runtime only:** proceed with black-box exploration using contracts and observed behavior; identify the source-access limitation.
- **Source only:** hunt for code-level defects and risks, prepare targeted reproduction requests, and label runtime verification as blocked. Do not claim requests were executed.
- **Neither available:** request a repository/path or test URL; describe the next step without inventing a target or findings.

Record the source revision and deployed build independently, including when their relationship is unknown. A local branch does not prove what is deployed. Use existing authorization for routine probes and disposable fixture changes. Clarify before crossing an unknown mutation boundary, affecting other users' data, or generating destructive, bulk, costly, or externally delivered effects. Continue independent analysis meanwhile.

## Read code to find plausible failures

Map the selected operation or workflow through routing, parsing/validation, authentication, authorization, domain logic, persistence, outbound calls, and error handling. Follow relevant dependencies; do not read the entire codebase by default. Read requirements and contracts alongside implementation. Code explains what may happen; it is not automatically the authority for what should happen. Record conflicting or ambiguous expectations explicitly. Treat comments and test expectations as evidence to check, not as independent proof of the requirement. Stop the initial reading pass once you can name the main risks and design a useful probe; return to source when an observation raises a new question.

Actively look for defects: missing ownership checks, client-controlled privileged fields, validation that is declared but never executed, partial writes, inconsistent state transitions, swallowed errors, retry duplication, stale reads, or sensitive response fields. Select concerns grounded in this code and domain, rather than attaching every possible risk to every endpoint.

Inspect relevant existing tests and their assertions, inputs, and mocked boundaries. Distinguish inspected tests from tests actually run. A filename, green suite, or coverage percentage does not prove that a business rule is protected. Missing test coverage is a risk or test gap, not itself a product defect.

Keep a compact, evolving risk map:

| Area / behavior | Evidence and plausible failure | User impact | Existing protection / uncertainty | Priority and next probe |
| --- | --- | --- | --- | --- |

Prioritize using impact, exposure, complexity/change, weak evidence, and likelihood supported by context. Explain the ordering briefly; avoid invented probabilities. Convert important suspicions into testable hypotheses: what input, identity, or sequence would expose the problem, and what observation would contradict it? When source access exists, use that analysis to choose runtime probes, not merely to explain failures afterward.

## Explore the running API

Choose a short session charter: the question, feature boundary, explicit exclusions, key risks, and stopping condition. Honor the user's time/request budget. Reserve time to preserve evidence and deliver a usable report; write down important findings as they emerge. Otherwise start with a bounded pass through the highest-priority risks and reassess at meaningful checkpoints. Routine scope and probe choices do not need a plan-approval ceremony.

Use **curl**, HTTPie, an available language HTTP library, or another HTTP client that exposes the request, status, headers, body, and timing. Prefer available tools and existing authentication helpers; a dedicated testing framework is unnecessary. Check client help when flags are uncertain. Use explicit request timeouts. Preserve error bodies for negative probes; do not mistake an HTTP client's success exit code for a correct API result.

Check a representative read for usable application behavior before launching a probe batch. If it returns a gateway/service-unavailable response, stop the batch and use only a few targeted availability checks within the user's limit. A script must stop on that condition too; do not run planned mutation, cleanup, or validation matrices against repeated outage responses. Report functional testing as blocked, retain the availability evidence, and continue useful source analysis if available. A reachable proxy or a successful health check alone does not prove that the feature is usable.

For the selected risks, consult the relevant techniques in [experiment design](references/experiment-design.md), including relationships between results, state transitions, ownership contrasts, and ambiguous write outcomes. Establish a representative valid request, then vary inputs, identity, and state to test the risk hypotheses. These are testing lenses, not a mandatory case matrix.

Inspect the whole observable result. A status code alone is insufficient: check response semantics, relevant headers, follow-up reads, and resulting state. Failed requests may still mutate data; successful ones may fail to persist it. Distinguish ordinary live behavior from injected conditions, mocks, and proxy/gateway behavior. For streaming APIs, inspect event semantics, ordering, completion, and interruption rather than treating every transport chunk as an event.

Compare observed behavior with the agreed requirement and the applicable contract version, including referenced schemas. Classify implementation defects, documentation defects, and unresolved product decisions separately. Do not invent a required status code or update documentation merely to legitimize faulty behavior.

For suspicious results, capture the smallest reproducible request and check alternative explanations such as stale fixtures, expired credentials, shared quotas, or build mismatch. Stop repeating probes that add no evidence; preserve intermittent findings with actual reproduction counts and conditions. A credible unresolved suspicion belongs in the report even when reproduction is blocked. Preserve the first failure before simplifying the reproduction, and separate fresh-state runs from retries that reuse mutated fixtures.

## Evidence, findings, and completion

Keep a durable session report and sanitized evidence in the user's chosen reporting location or existing project convention. If neither exists, create `report.md` and an `evidence/` directory. As you test, record meaningful checks with passed/failed/blocked/not-run outcomes and links to HTTP request/response evidence; retain a follow-up state read for claims about persistence. Summarize the operations and states explored, including passing contrasts, so another tester can see what was checked. Use [the report guide](references/reporting.md) for the evidence package, risk summary, finding template, stable IDs, type labels, severity rationale and retest status. Read existing relevant findings to avoid duplicates. Include functional, documentation or performance findings when supported and in scope; keep issue type separate from evidence state and honor explicit exclusions.

Capture method/path, sanitized inputs and role, status, pertinent headers/body, state before/after, environment, and observed reproduction count. Use named placeholders for credentials; keep executable secret-bearing requests and raw responses out of published evidence and Git. Preserve enough sanitized detail to reproduce the finding without relying on an inaccessible scratch file.

Assess observed impact before assigning severity. Separate runtime-confirmed failures, code-evidenced findings, suspected causes, documentation mismatches, and untested consequences. Report important findings as they emerge, then continue unaffected work. Report evidence of no defect in the tested cases just as honestly as failures; never manufacture bugs to meet a quota.

Finish when the scoped important risks have credible evidence, promising anomalies are reproduced or explicitly unresolved, and further probes yield little useful information—or the user's budget ends. Clean up only the session's disposable resources and connections; record anything remaining. Summarize findings, prioritized residual risks, explored behavior, blocked/untested areas, and the next useful action. Never call a source-only review a completed runtime exploration or claim exhaustive API coverage.

Recommend focused regression cases at the lowest level that can detect each failure, with representative API checks for genuine integration risks. Keep one-off exploratory breadth separate from the eventual suite size. Creating a regression suite, changing product code/contracts, filing external issues, publishing reports, or editing this skill requires scope that includes those actions; the exploration request alone does not add them.
