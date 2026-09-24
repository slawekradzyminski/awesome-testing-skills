# Historical project comparison — protocol

Status: admitted protocol, frozen with the case manifest before candidate execution. This document is not a result.

## Question and treatment

Does the existing exploratory testing skill add useful behavior beyond an ordinary request or a compact reporting template when an agent must choose investigations in a real project's original context?

Retain the exact skills identified in development/treatment-decision.json. Development evidence consists of the completed earlier studies, including failures; no new guidance is tuned to the historical cases. Case selection is performed by a fresh curator denied access to the skills and prior results. The coordinating author validates the selected runtimes and knows their expected failures. This is separation of roles, not independent human research or a guarantee against model pretraining exposure to public repositories.

Three conditions: normal request; the same request plus the existing report template; the same request plus explicit use of the full API/UI skill. All get the same source/documentation access, test instance, credentials, tools and budget for a given task. No detailed reporting contract or testing checklist is added to the normal condition. All conditions retain ordinary coding-agent instructions and the shared Playwright CLI helper. Disable other discoverable skills, project AGENTS intake, user configuration and app connectors per process; verify this with a preflight.

## Cases and admission

Target six tasks: four distinct historical functional failures, one corrected control and one intentionally unavailable API. Require an observable, reproducible user-facing difference on the historical before/fix pair. Verify it twice per revision using real HTTP/browser behavior. Reject documentation-only changes, newly introduced feature requirements, artificial source mutations and exceptions visible only in evaluator logs. Record all screened/rejected proposals. If a case is infeasible, record the replacement or reduced design before freezing, never after seeing candidate performance.

Supply unchanged original project source and documentation at the selected revision. Candidates receive full ordinary source context, not a curated selection of changed files. Remove Git history and instruction/config files equally; do not give them the fixing commit, new regression tests, patches, issue description, expected results or this protocol. For corrected controls, retain ordinary tests that belong to that revision and disclose that asymmetry in interpretation. A corrected case is not asserted to be free of other bugs.

Build real historical Java/React applications. Keep compiler/runtime adaptations, database seeds, gateway behavior and compatible backing-service revisions explicit. No source mutation is used to manufacture failures. Controlled latency forwards actual backend responses without changing their bodies; its presence is disclosed, and it is not itself scored as a performance failure. Missing optional external services are shared fixture limits, not extra discovery credit.

## Admitted tasks and runtime qualifications

The independent curation admitted H1 (duplicate-email registration), H3 (false-empty cart during detail loading), H4 (mobile product-detail overflow) and reserve H5 (stale cart quantity after refetch). H2, a missing-token filter exception, was excluded because its wire response was identical before and after the fix. H5 requires a second client edit plus a real reconnect-triggered refetch; focus-only attempts failed and are retained. No case was chosen using candidate outcomes.

H1 uses its original Java21 backend revision. H3/H4 and the H4 corrected control use their original React bundles plus backend b4973a5 (full revision in sources.json). H5 uses the original March React bundle with compatible November backend 75ca60d; its hardcoded localhost:4001 API and UI port 8081 require an exclusive two-port lock. The wrapper serves its UI at `127.0.0.1:8081` so browser navigation reaches the IPv4 study gateway even when an unrelated IPv6 service answers `localhost`. It serves unchanged production bundles and forwards native backend responses. It adds 1.8 seconds to product-detail GET response delivery in modern UI cases and 80 milliseconds to other UI GETs. Legacy product paths receive only the latter. Browser offline/online intervention is available equally through the browser tool; the candidate prompt does not suggest it.

The catalog contains three controller-created products including one long, valid identifier-like name, using the actual product API, plus a pre-populated customer cart. Legacy native seed data also remain. These are explicit test fixtures, not sampled production data. The candidate's account credentials and allowed data mutations are shared equally. Gateway CSP prevents external page resources; optional image/external-link, email, SSO, LLM and traffic features are disclosed exclusions. Ordinary application source, tests, scripts, manifests and docs are retained; Git data, automation directories, AGENTS.md and CLAUDE.md are removed equally. Compiled assets are separately hashed; candidates see original source rather than evaluator-built binaries.

The unavailable task uses an intentionally 503-returning loopback gateway with the corrected H1 source available. It does not launch the native application. Handling this condition is separate from finding historical faults. The corrected-control task retains its revision's original regression tests; it has richer evidence of protection than the before snapshot and does not enter defect discovery denominators.

## Schedule and execution

Six tasks × three conditions × two fresh sessions = 36 attempted runs once admitted. Schedule arm permutations across task/repetition blocks. Use requested model gpt-6-astra with high reasoning, the same recorded CLI and browser tooling. Eight minutes includes reading, testing and reporting; 180 proxied API requests and 100 browser actions. Up to three candidates run concurrently, each on its own application state. Any legacy fixed-port case must hold an exclusive lock for its ports. Record startup and cleanup separately from candidate elapsed time.

Use fresh ephemeral CLI sessions. Candidate/controller separation is a context boundary, not an OS sandbox: local shell permissions needed by the browser are broad. Record source/skill hashes and inspect traces for boundary violations. No source repository edits, real accounts, public mutations or external issue filing. Stop owned runtimes and browser sessions even on failures.

Keep all attempted runs. Runtime startup failure is an infrastructure outcome, not a model miss. A timeout or model error is retained, not silently replaced. The controller ends a candidate at 480 seconds, retains partial artifacts, and records cleanup separately. Browser-action totals require trace review and remain unknown where not reconstructable. Do not infer complete action counts from CLI invocation counts. Record available token usage without estimating a monetary bill.

## Outcomes fixed before runs

Do not create a single weighted overall score.

For historical functional tasks, report known faults identified and runtime-actionable findings separately. A known fault is actionable only if candidate evidence establishes its actual mechanism/user consequence and offers a reproduction another tester could follow in the supplied environment. A controller audit may corroborate the candidate's evidence, not fill in missing observations. Code suspicions remain a separate outcome.

Also assess every additional claim: valid and actionable, valid but incomplete, unsupported, unresolved intent, or outside scope. Deduplicate symptoms sharing one independently fixable cause. Suggestions and honestly qualified risks are not false positives. Accept genuine new defects in corrected controls. Separate fixture-induced behavior and version compatibility issues from product defects.

Developer handoff: for each substantiated finding, record whether the recipient has enough information to reproduce (environment/state/steps), understand demonstrated user impact, and tell whether a correction works. Report missing information explicitly. Neither severity labels, template compliance nor report length earn points by themselves. This is artifact-based actionability, not a measured developer productivity study.

Passing/control outcomes require concrete executed observations and bounded claims. Outage outcomes require recorded availability evidence, an explicit distinction between blocked runtime testing and executed source/unit checks, proportionate stopping, and a specific useful next action. Report availability request/mutation counts directly; do not hide excessive probing inside a weighted score. No invented functional pass or confirmed runtime defect is acceptable when runtime was unavailable. Source-backed hypotheses are allowed with honest evidence labels.

Assess coverage selection against the actual assigned task: did observed experiments address meaningful user risks, and are material omissions disclosed? Retain cited examples, not a checklist count. Report request counts, candidate elapsed time, output/cached/input tokens, integrity and cleanup separately. Compare like-for-like tasks; keep unavailable and corrected-control handling separate from defect discovery denominators.

## Review and interpretation

Fresh artifact reviewers receive case source/context, candidate reports/evidence, the frozen oracle and audit data; condition labels and skill files are withheld. Text may reveal guidance, so describe review as partially masked. Reviewers must inspect cited artifacts and screenshots for visual claims. Preserve raw reviews. Any owner adjudication must identify the original judgment, evidence and reason and be applied consistently across arms. Independently reproduce material additional findings before treating them as established.

A skill improvement requires supported task-level benefit in actionable findings, accuracy or useful handling over both alternatives. Small subjective differences and one-off successes are descriptive, not statistical evidence. A tie or regression is a valid outcome. Fewer API calls alone do not prove efficiency when coverage differs; shared-host execution limits timing comparisons. Public historical code can have appeared in model training. These few tasks from the user's projects are not a representative industry sample. Publish limitations and unsuccessful results alongside successes. Subsequent tuning or extra cases require a separately labelled future study.
