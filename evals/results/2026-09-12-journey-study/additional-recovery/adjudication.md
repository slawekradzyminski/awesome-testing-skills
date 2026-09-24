# Additional draft/recovery observations

The study author independently reproduced both observations on fresh corrected source without changing application code. Screenshots were captured and opened; commands and state results are retained. All owned processes and browser sessions were closed.

## Draft loss during loading

An ordinary selection of A100 starts its documented 700 ms lookup. The instruction textarea remains enabled while old order details are displayed. Text entered through an ordinary fill during this interval is replaced when the lookup finishes. This is observed draft loss, not a claim that intentional latency is a defect. Treat as a valid usability/state-consistency issue with Medium suggested severity, and explain that disabling the editor during loading or preserving the correctly associated draft are possible outcomes. It is separate from a stale response overwriting a different selected order.

## Transport recovery

Aborting one note POST before it reaches the server leaves Save disabled and feedback empty. After removing interception, a GET succeeds but Save remains disabled. Reload restores the control and replaces the unsaved draft with persisted content. Treat as a conditional recovery defect/gap, explicitly identifying the injected failure and the extension of the brief's recoverable-failure intent to transport errors. Do not claim a spontaneous outage, real data corruption or an explicit offline-storage requirement. Medium suggested severity reflects the blocked retry and manual copy/reload workaround.

Apply these decisions consistently to equivalent claims in all conditions. They are additional findings, not changes to the seeded recall denominator. Where a candidate leaves the expectation unresolved instead of claiming a defect, preserve that qualification.
