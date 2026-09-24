# Additional finding: delivery service response ordering

A template-condition candidate reported this previously unseeded problem. The study author independently reran its ordinary-click reproduction on a fresh corrected fixture. Both real server writes returned 200: express first, then standard. Delaying delivery of the first response by one second caused the UI to show express while an authenticated read and subsequent reload showed standard. The response bodies were retained unchanged; only delivery timing was controlled. The screenshot was captured and opened.

This supports a conditional UI state-consistency defect in `setService`, separate from the seeded order-detail lookup race. It does not establish occurrence frequency on an uncontrolled network. Suggested severity: Medium, because visible service confirmation contradicts persisted selection. The fixture source, request records, commands and results are retained here. No fixture code was changed; the owned browser and server were stopped.

Apply this adjudication to equivalent claims in every condition. The corrected variant removes the registered seeds, not every possible application fault. This additional discovery does not alter the frozen seeded-recall denominator.
