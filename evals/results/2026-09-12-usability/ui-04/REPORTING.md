# Evaluation output contract

Write your normal exploration report to `report.md`, evidence under `evidence/`,
and a compact `submission.json` with this shape (fill actual values):

```json
{
  "source_access": true,
  "runtime_exercised": true,
  "runtime_status": "tested",
  "checks": [{"name": "specific behavior checked", "basis": "runtime",
    "status": "passed", "expected": "requirement", "actual": "observed result",
    "evidence": ["evidence/http.txt"]}],
  "findings": [{"requirement_id": "use the applicable requirement ID, or UNMAPPED",
    "title": "observable problem", "status": "confirmed or code-evidenced or suspected",
    "expected": "requirement and basis", "actual": "observed behavior",
    "impact": "demonstrated consequence", "evidence": ["evidence/reproduction.txt"]}],
  "risks": [{"area": "behavior", "reason": "evidence", "priority": "high/medium/low", "next_probe": "next useful experiment"}],
  "observations": [{"method": "GET", "path": "/api/v1/cart", "status": 200,
    "action": "what prompted the request", "evidence": "evidence/http.txt"}],
  "limitations": ["meaningful untested scope or constraints"],
  "cleanup": "what was restored or remains"
}
```

Use runtime_status `tested`, `blocked`, or `not-run`. runtime_exercised means
functional application behavior was exercised; merely attempting availability
checks does not make it true. For each check use basis `runtime` or `source`
and status `passed`, `failed`, `blocked`, or `not-run`. Cite actual evidence for
passed/failed/blocked checks; proposed unexecuted checks may have empty evidence.
Report which checks passed even when there are no findings. Do not equate a green
subset with a defect-free application. Describe missing access and concrete next
inputs that could improve coverage, without promising they will reveal more bugs.
Empty findings/observations are valid when justified. Distinguish code evidence
from runtime confirmation. Evidence paths must be relative to this directory.
Include screenshots you actually opened when reporting UI observations.
Do not change the application, requirements, skills, or existing tests.
Use only this candidate directory and the assigned runtime; do not look for
grader files, other runs, the parent repository, or external copies of this app.
The fixture/process owner will stop the server after you finish. Close only
your own browser session. The assessment is of exploration, not bug fixing.
