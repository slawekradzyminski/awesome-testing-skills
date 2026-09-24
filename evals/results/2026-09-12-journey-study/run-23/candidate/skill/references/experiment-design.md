# Designing useful API experiments

Read this when choosing live probes or designing reproductions from a source-only review. Select techniques that answer the current questions; do not execute every example for every endpoint.

## Choose the oracle and the observation

Name the rule the experiment challenges and where it comes from. Requirements, an agreed contract, and established domain invariants can support expectations. Existing code, comments, or tests may all repeat the same misunderstanding. Conflicts between them are a finding to investigate, not a reason to choose whichever makes the response pass.

When an exact answer is difficult to predict, compare related operations against a justified relationship. For example, a failed update should preserve existing state when the contract promises atomicity; filtering should not introduce records outside the filter. Check preconditions such as concurrent changes, rounding rules, caching, or asynchronous processing before concluding that the relationship was violated. Do not assume adding and removing an item reverses all effects if fees, audit history, or reservations are part of the product.

## Match the probe to the risk

| Evidence or question | Useful experiment | What to inspect |
| --- | --- | --- |
| Validation or parsing may be bypassed | Compare a valid value with one meaningful boundary, missing/null distinction, or type change | Parsed meaning, public error contract, and absence of unintended writes |
| Authorization is present but ownership is unclear | With controlled users A/B, compare A's access to A's resource and B's resource | Response fields and actual read/write authorization, not only different status codes |
| A business workflow depends on earlier steps | Omit, repeat, or reorder a relevant transition using disposable state | Whether the invariant holds across requests and whether partial state remains |
| Update behavior looks inconsistent | Capture state, update one field, then read it through the relevant public interface | Changed field, unrelated fields, version, and preservation of required relationships |
| Lists, filters, or pagination may lose data | Use a small known dataset and compare adjacent pages or equivalent query forms | Membership, ordering, duplicates and omissions under recorded sort/stability assumptions |
| A client can influence privileged or server-owned fields | Compare a legitimate update with a targeted extra-field variation | Which values are accepted, ignored, returned, and actually persisted |

Start with a small discriminating contrast. Vary one factor to establish a cause, then combine factors when the code or observations suggest an interaction. Do not stop all boundary exploration merely because validators have unit tests: a public-route check can reveal that validation is never invoked. Conversely, do not reproduce every unit-test permutation at the HTTP level without a distinct question.

## Investigate uncertain write outcomes

A timeout or lost response does not establish that the server performed no work. Before retrying a mutation, use an available operation/resource identifier, read endpoint, or relevant logs to determine whether it took effect. Do not automatically replay an uncertain write unless the contract or other evidence makes that appropriate. Preserve request identifiers and separate the original attempt from retries. HTTP idempotency concerns the intended server effect, not identical responses to every repetition. [RFC 9110, §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)

Likewise, `202 Accepted` does not establish completion. Inspect the API's documented completion signal with bounded polling where available. Record intermediate and terminal states separately; an eventual-consistency delay is not automatically a lost write. When the completion window is unspecified, report the observed delay and uncertainty instead of inventing an SLA. [RFC 9110, §15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3)

Concurrency probes need an explicit invariant and a small controlled interleaving, such as two updates reading the same version. Use disposable fixtures and remain within the agreed request budget. A concurrent race investigation is not permission to generate load.

## Reduce noise without erasing the failure

Save the first request, response, role, and state before minimizing. Remove one unnecessary field or step at a time while keeping the failure reproducible. Prefer unique fixture identifiers and record setup/cleanup so another session cannot silently change the experiment. Do not treat a probe that passes only after a failed attempt mutated its fixture as a clean pass.

Check whether an apparent product defect comes from an expired identity, permissive schema, proxy behavior, mock, shared quota, or different deployed version. Preserve intermittent evidence; distinguish “not reproduced again” from “disproved.” Broaden the investigation only when the next probe can materially improve the conclusion.
