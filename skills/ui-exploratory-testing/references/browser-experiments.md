# Browser experiments and evidence

Read this when choosing or performing live UI experiments. The techniques are optional lenses; evidence requirements apply to the claims you actually make.

## Design a probe that can change your conclusion

- **Anchor expectations outside the implementation.** Start from the user outcome or agreed design. A UI and backend can agree while sharing the same business mistake. If the rule is unclear, investigate consistency and label the unresolved expectation.
- **Seek a disconfirming case.** After a suspicious result, try the nearest ordinary state in which your explanation predicts a different result. A Cancel action that saves only with valid data points toward form submission; indiscriminately changing many inputs would obscure that distinction.
- **Explore transitions, not only screens.** Consider entering, leaving, cancelling, returning, refreshing, and recovering after failure. An addressable route or completed step may be reachable with stale or missing prerequisite state. Choose the transitions that matter for this journey.
- **Change one factor, then combine deliberately.** Isolate the effect of a field, role, or action first. Then examine a plausible interaction suggested by the code, such as a delayed response after navigation or an expired session during submission. A Cartesian product of every state and viewport is unnecessary.
- **Use meaningful data variation.** Long translated labels, empty collections, large result sets, timezone boundaries, or Unicode input can expose assumptions. Choose variations tied to the product's audience and rules; do not invent locale or device support requirements.
- **Distinguish observation channels.** A toast, an HTTP response, and a fresh persisted-state read establish different things. Use a reload, another relevant view, or a read API to challenge optimistic or cached UI state. Do not count several displays of the same cached value as independent confirmation.
- **Keep the browser experiment authentic.** Use normal controls and user input for the behavior under investigation. DOM edits, forced clicks, or injected JavaScript that bypass disabled controls/validation can be useful diagnostic interventions, but must be labeled and followed by an ordinary-user reproduction before claiming that path is user-reachable.
- **Preserve order and isolation.** Record the starting state and the sequence that produced a failure. Try a new context or fresh fixture when stale state might explain it, while retaining the original evidence. For ordering/race questions, control response timing deliberately instead of repeatedly clicking until something breaks.

Prioritize experiments that distinguish plausible causes or expose substantial risk. Switch to another risk when repeated probes teach nothing new. A blocked line of inquiry should have a concrete missing observation and next step, not an endless sequence of retries.

## Visual and responsive exploration

Capture **and open** screenshots for relevant visual states. Inspect composition and grouping as well as clipping, overflow, alignment, legibility, missing content, and feedback. DOM/accessibility snapshots help explain behavior but do not replace visual inspection. Do not hide or restyle suspicious content to produce a clean screenshot. If images cannot be viewed, report visual review as incomplete.

Use the product's supported viewport/device targets. If unknown and responsive testing is in scope, choose representative narrow, intermediate, and wide CSS viewports and record the actual sizes as sampling choices. Inspect relevant breakpoint transitions and opened menus/dialogs, not only their closed triggers. Select states by risk rather than generating a screenshot gallery. Desktop resizing checks responsive layout; it does not establish real-device, mobile keyboard, Safari, or screen-reader coverage.

Investigate visible concerns with contrasting states, nearby widths, or measurements. Explain user consequences and separate observed impairment from subjective design preferences. Check keyboard behavior and accessible semantics where relevant; support precise contrast or standards claims with measurement and the applicable standard. Do not equate a screenshot or automated accessibility scan with a complete accessibility assessment.

## Network, console, and timing evidence

Begin collecting relevant network observations before the action being investigated, then actually inspect them. Associate actions and starting state with expected and forbidden effects, request method/path/count/status, and the resulting UI/backend state. Include successful requests and actions expected to make no mutation. If logs are cumulative, compare request identifiers or bounded before/after captures. Observe relevant pending requests through completion/failure; qualify absence claims by the observation window.

Use an available HTTP client for setup, follow-up reads, or cleanup when useful and authorized, while keeping UI behavior under investigation exercised through the browser. Do not replace the tested UI action with a direct API request. If network inspection is unavailable, state the gap and verify side effects by other available evidence without claiming unseen traffic was checked.

Inspect console/page errors around the action and distinguish expected negative responses, injected failures, and tool errors from application defects. For suspicious latency or duplication, repeat a focused measurement and record sample count, cache/network/device conditions, and user consequence. Do not invent an SLA or generalize a local measurement to field performance.

## Further guidance for workflow risks

[OWASP WSTG: workflow circumvention](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/10-Business_Logic_Testing/06-Testing_for_the_Circumvention_of_Work_Flows/) offers additional ideas for examining missing, repeated, and reordered steps. Use the relevant business-flow questions within the agreed scope; loading this reference does not turn a UI exploration into a full security assessment.
