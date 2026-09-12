# Evaluation output contract

Write your normal exploration report to `report.md`, evidence under `evidence/`,
and a compact `submission.json` with this shape (fill actual values):

```json
{
  "source_access": true,
  "runtime_exercised": true,
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

Empty findings/observations are valid when justified. Distinguish code evidence
from runtime confirmation. Evidence paths must be relative to this directory.
Include screenshots you actually opened when reporting UI observations.
Do not change the application, requirements, skills, or existing tests.
Use only this candidate directory and the assigned runtime; do not look for
grader files, other runs, the parent repository, or external copies of this app.
The fixture/process owner will stop the server after you finish. Close only
your own browser session. The assessment is of exploration, not bug fixing.
