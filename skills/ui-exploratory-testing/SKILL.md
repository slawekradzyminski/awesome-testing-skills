---
name: ui-exploratory-testing
description: Explore web interfaces through focused source-code analysis and live browser experiments, identify risky user journeys, and report functional, visual, accessibility, and network findings. Use for exploratory UI testing and code-informed bug hunting; regression-suite implementation is a separate task.
---

# UI Exploratory Testing

Explore as a tester trying to uncover consequential failures. Use application code to identify risks, then challenge those hypotheses through the real interface. Follow unexpected behavior and user impact rather than executing a fixed inventory of clicks.

## Establish the target and invite source access

Start from the user's request, existing conversation, and applicable repository instructions. If source has not been supplied or located, encourage the user to provide the frontend repository/path and branch or revision, plus backend code or API contracts for relevant flows. Explain that code access reveals hidden states, event handling, permission checks, and integration risks. Prefer relevant files or repository access over a complete code dump; never ask for secrets in chat.

Establish the application URL, intended user outcomes, screens/journeys in scope, available test roles, supported browsers/devices if known, and permissible data changes. Reuse available context. Locate source through supplied project links/configuration without searching unrelated private projects. Ask only for missing details that affect the next step, and do not repeatedly request code the user cannot share.

- **Source and runtime available:** combine focused code analysis with browser exploration.
- **Runtime only:** proceed with black-box exploration, naming the missing implementation context.
- **Source only:** identify code-evidenced defects and risks, propose targeted browser reproductions, and label runtime/visual verification as blocked. Do not invent screenshots or executed interactions.
- **Neither available:** request a repository/path or test URL without inventing a target or findings.

Record source revision and deployed build separately, including unknowns. Do not assume the branch matches the running UI. Reuse existing authorization for routine interactions and disposable fixtures. Clarify before affecting other users' data or triggering destructive, bulk, costly, or externally delivered effects beyond the agreed scope; continue independent analysis meanwhile.

## Read code and map risky journeys

Trace the selected user journey through routes, components, forms, event handlers, client state, API calls, authorization, and relevant backend behavior. Read enough dependencies to understand failure paths without scanning the whole application by default. Compare requirements/design intent with implementation; current behavior is not automatically correct.

Hunt for concrete failure mechanisms: unintended form submission, duplicate handlers, stale async responses, optimistic updates without rollback, client-only permission enforcement, state lost on navigation, misleading success feedback, inaccessible controls, and layout constraints that can hide content. Select concerns grounded in this UI rather than treating these examples as a universal checklist.

Inspect relevant tests, assertions, fixtures, and mocked boundaries. A page object or passing test does not establish coverage of the journey's important states. Distinguish inspected from executed tests; missing coverage is a risk, not a product bug.

Keep a compact, evolving risk map:

| Journey / state | Evidence and plausible failure | User impact | Existing protection / uncertainty | Priority and next experiment |
| --- | --- | --- | --- | --- |

Prioritize important user outcomes, permissions/data boundaries, uncertain transitions, recent changes, and weakly tested integrations. Explain priorities through evidence and impact without invented probabilities. Form hypotheses with an observable failure and a contrasting case that could disprove them. Use the source analysis to guide the first experiments, then adapt to runtime discoveries.

## Explore with a browser agent

Prefer **Playwright CLI** and load its skill if available. Otherwise use the CLI's current help/documentation. An available browser agent, Playwright MCP, browser DevTools integration, or comparable browser-control tool is a valid alternative. Honor the user's selected browser/tool. If the preferred tool is unavailable, use a capable existing alternative and describe any observation limits; do not install tooling or change global configuration merely to enforce a preference.

Use the chosen tool's documented interface and fresh page snapshots/observations to target controls; do not invent element references or assume the UI matches source. A dedicated session is useful when supported. Control and clean up only the session you created, not the user's other browser sessions.

Write a lightweight charter: user outcome, feature boundary, key risks, and stopping condition. Honor user time/action limits; otherwise start with a bounded pass through the highest-priority risks and reassess at meaningful checkpoints. Choose experiments autonomously within the authorized scope. Follow promising anomalies without requesting permission for each click or multiplying every state by every device size.

Establish a representative working journey. Then vary meaningful combinations of data, role, state, sequence, and timing. Useful lenses include:

- **Intent and side effects:** compare what a control promises with visible, network, and persisted outcomes. Cancel, Back, and navigation can mutate state accidentally when a form is valid.
- **State and recovery:** retries, validation/server errors, refresh, direct links, session expiry, unsaved edits, loading/empty states, and returning to a journey.
- **Timing:** duplicate clicks, late responses, stale tabs, and interrupted requests. Use controlled delays or failure injection only for a concrete question within scope; label injected conditions and remove them afterward.
- **Roles and business rules:** permitted and forbidden actions, meaningful field relationships, ownership boundaries, and sensitive data displayed or returned to the client.
- **Perception and access:** responsive layout, keyboard navigation, focus, names/roles, errors, menus/dialogs, and the ability to complete the intended task.

Read current state after significant actions. Prefer observable readiness over arbitrary sleeps. Validate the business outcome, including state after navigation/refresh and relevant read APIs when available. A toast, correct destination URL, or quiet console is insufficient evidence of successful persistence.

### Visual and responsive exploration

Capture **and open** screenshots for relevant visual states. Inspect composition and grouping as well as clipping, overflow, alignment, legibility, missing content, and feedback. DOM/accessibility snapshots help explain behavior but do not replace visual inspection. Do not hide or restyle suspicious content to produce a clean screenshot. If images cannot be viewed, report visual review as incomplete.

Use the product's supported viewport/device targets. If unknown and responsive testing is in scope, choose representative narrow, intermediate, and wide CSS viewports and record the actual sizes as sampling choices. Inspect relevant breakpoint transitions and opened menus/dialogs, not only their closed triggers. Select states by risk rather than generating a screenshot gallery. Desktop resizing checks responsive layout; it does not establish real-device, mobile keyboard, Safari, or screen-reader coverage.

Investigate visible concerns with contrasting states, nearby widths, or measurements. Explain user consequences and separate observed impairment from subjective design preferences. Check keyboard behavior and accessible semantics where relevant; support precise contrast or standards claims with measurement and the applicable standard. Do not equate a screenshot or automated accessibility scan with a complete accessibility assessment.

### Network, console, and timing evidence

Begin collecting relevant network observations before the action being investigated, then actually inspect them. Associate actions and starting state with expected and forbidden effects, request method/path/count/status, and the resulting UI/backend state. Include successful requests and actions expected to make no mutation. If logs are cumulative, compare request identifiers or bounded before/after captures. Observe relevant pending requests through completion/failure; qualify absence claims by the observation window.

Use an available HTTP client for setup, follow-up reads, or cleanup when useful and authorized, while keeping UI behavior under investigation exercised through the browser. Do not replace the tested UI action with a direct API request. If network inspection is unavailable, state the gap and verify side effects by other available evidence without claiming unseen traffic was checked.

Inspect console/page errors around the action and distinguish expected negative responses, injected failures, and tool errors from application defects. For suspicious latency or duplication, repeat a focused measurement and record sample count, cache/network/device conditions, and user consequence. Do not invent an SLA or generalize a local measurement to field performance.

## Report and finish

Use [the report guide](references/reporting.md) for findings, a prioritized risk summary, and meaningful coverage gaps. Keep one local session report unless the user/project has another convention; link existing findings rather than duplicating them. Preserve essential sanitized evidence with the report so it remains actionable outside the scratch workspace.

Separate runtime-confirmed failures, code-evidenced findings, hypotheses, and unresolved design decisions. Reproduce anomalies minimally, test alternative explanations, and assess impact before severity. Report important findings as they emerge and continue unaffected exploration. Do not invent findings to meet a quota or silently dismiss a concern whose intent remains unresolved.

Finish when important scoped risks have credible evidence, promising anomalies are reproduced or explicitly unresolved, and further probes add little information—or the user's budget ends. Revisit what was assumed but never observed. Remove session-owned mocks/interceptors, clean up disposable fixtures and your browser session, and report leftovers. Summarize bugs, prioritized residual risks, explored journeys/states/viewports, blocked checks, and the next useful action. Qualify positive conclusions by actual observations; never claim exhaustive UI coverage.

Recommend a small set of valuable regression scenarios, including forbidden side effects when relevant. One-off exploration may be broader than the permanent suite. Product fixes, regression-suite implementation, external issue filing, report publication, and edits to this skill require scope that includes those actions; an exploration request alone does not add them.
