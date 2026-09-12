# API exploration report

Adapt this structure to the existing reporting system and size of the task. Keep one independently fixable problem per finding. A small session can contain its findings inline; link existing bug records when appropriate.

## Session summary

- **Question and scope:** requested operations/workflow, exclusions, time/request limits.
- **Environment:** date, base URL, configuration, test roles, source revision, deployed build, and whether they match (or unknown).
- **Expected behavior:** requirement/contract version and unresolved product questions.
- **Results:** consequential findings first, followed by explored behavior and material gaps.

| Area / risk | Evidence or reason for concern | Impact and exploration priority | Probe / observation | Status and next action |
| --- | --- | --- | --- | --- |

Useful statuses: explored with no defect observed, runtime-confirmed finding, code-evidenced finding (not reproduced), suspected, blocked, not explored. Keep untested risks distinct from confirmed bugs. Exploration priority and bug severity serve different purposes.

## Finding

**Title:** METHOD /path — observable problem

**Classification / evidence state:** functional, contract/documentation, or needs clarification; runtime-confirmed, code-evidenced, or suspected.

1. **Preconditions and reproduction:** role, test data state, minimal steps and sanitized request. Describe placeholders so another tester can substitute their own credentials safely.
2. **Actual result:** status, pertinent headers/body, resulting state, and actual reproduction count. Include essential evidence inline and link larger sanitized artifacts.
3. **Expected result and basis:** requirement or contract location; explicitly label a proposed expectation if intent is unresolved. For documentation mismatches, name the exact operation/schema/property and conflicting declaration.
4. **Impact:** affected user/workflow, demonstrated consequence, scope, workaround, and uncertainty. Do not present hypothetical exploitation or downstream failure as observed fact.
5. **Severity:** apply the project's scale after assessing impact. If none exists, use High for demonstrated severe/core-flow impact, Medium for material impairment, Low for limited impact, or Unassessed when evidence is insufficient. Mark provisional assessments.
6. **Investigation:** source file/line and revision, likely cause clearly labeled, alternative explanations checked, and unresolved questions. For source-only findings, distinguish the defect's code evidence from unverified runtime reachability.
7. **Retest and regression suggestion:** the required observable correction, neighboring behavior worth checking, and the lowest useful test level. A proposed fix is not a verified fix.

## Closeout

Record tested and untested behaviors, residual risks in priority order, environment/tool limitations, and cleanup performed or still needed. State whether relevant existing tests were inspected, executed, failed, or unavailable. Mark a finding verified only after retesting the identified build. Keep raw secrets, tokens, cookies, private data, and unreviewed captures out of shared reports.
