# Claude Opus 5.5 evaluation and evidence-package smoke check — September 24, 2026

## What this result can establish

The new [four-arm API pilot](../journey-study/claude-ablation.md) separates investigation guidance from reporting guidance and scores **candidate-observed runtime state** from the server audit, without reading report wording. It is a development check on the previously used Dispatch Desk fixture. This fixture already produced a discovery ceiling, so these runs **do not establish that the skills improve bug discovery**. The [frozen inputs and per-run evidence](2026-09-24-claude-ablation/) are retained here.

Claude Code 2.1.281 requested and resolved `claude-opus-5-5` at high effort. Each arm received the same source, requirements, loopback app and task. The four candidates ran concurrently, one fresh session per arm, with a six-minute limit, 120-request limit and $1.50 per-run client cost cap. The CLI initialization exposed Bash, Edit and Read equally to all arms; the requested allowlist named six tools. No MCP servers or discovered skills loaded. These are one-run observations under shared-host contention, not a speed or cost comparison.

| Arm | Audit-observed seeded faults | API requests | Seconds | Estimated API cost |
| --- | ---: | ---: | ---: | ---: |
| Normal request | 3/3 | 43 | 61.84 | $0.1813 |
| Report guidance only | 3/3 | 49 | 80.34 | $0.2430 |
| Investigation guidance only | 3/3 | 44 | 92.23 | $0.2918 |
| Full skill | 3/3 | 31 | 58.92 | $0.1881 |

Every run completed, stayed within the time/request/cost limits, preserved its supplied source and guidance, and had no tool-path boundary flag. The deterministic scorer was rerun against each retained audit and matched the saved score. Eleven scorer tests pass, including a real-fixture calibration that scores the defective app 3/3 and the corrected app 0/3. A separately masked Opus 5.5 [artifact review](2026-09-24-claude-ablation/artifact-review.json) judged all twelve seeded findings actionable from the reports and their retained probe logs. Its masking is partial: report style may reveal guidance, and the reviewer did not receive every secondary file. It is not an independent human review.

Full Claude event streams and controller logs are retained in a private [local archive](/Users/slawek/benchmark-archives/awesome-testing-skills/opus55-ablation-and-evidence-20260924.tar.gz) (SHA-256 `9cb2ad6754ee224d0519b35176e30f6195f3f1dec50a874d9501190e247f74ed`); transient Claude configuration files were excluded.

The report review also found no clean reporting winner. The full-skill report called two rejected batch attempts independent confirmations despite reading the affected order only after both requests. The report-only arm called an over-refund in a simulated ledger “Critical” and described direct money loss; that impact was not observed. Padded-note behavior remained an unresolved interpretation across reports. These are secondary, evidence-dependent judgments; the primary audit score remains a tie at the ceiling.

## Evidence-package behavior check

After adding ticket-criteria intake and explicit artifact guidance, one fresh **UI skill** session against the corrected browser fixture produced a [report with five ticket-derived criteria and a ten-check ledger](2026-09-24-claude-ablation/evidence-smoke/ui/report.md), five linked [screenshots](2026-09-24-claude-ablation/evidence-smoke/ui/evidence/), a visit/state summary, and 11 relevant [HTTP exchanges](2026-09-24-claude-ablation/evidence-smoke/ui/evidence/http.jsonl). Seven checks passed and three were marked not run; no defect was invented. The screenshot for the out-of-order lookup and the 360-pixel view were opened and inspected. The report states which captures it opened and which response bodies were truncated. Its visit log is inline because the journey has one route.

One fresh **API skill** session produced a [report with a seventeen-check ledger](2026-09-24-claude-ablation/evidence-smoke/api/report.md), 32 saved [HTTP exchanges](2026-09-24-claude-ablation/evidence-smoke/api/evidence/http.jsonl), separate malformed-request evidence, and three runtime-confirmed seeded findings. The server audit records 34 API requests; the two malformed requests are retained separately. Both smoke sessions resolved to Opus 5.5, completed, and used disposable local data. The UI controller's post-run summary script had a local variable typo after it had already stopped the server and closed the browser; its completion, cost and artifact inventory were reconstructed from the retained Claude event stream. This accounting repair did not rerun or change the candidate's work.

These smoke checks show that the updated skill can generate the requested evidence package. They are one successful run per surface, with no no-skill counterpart, so they do not measure a skill effect or reliability. The conversational ticket-intake branch where no criteria are supplied was not exercised; both smoke tasks supplied requirements.

## Integrity and next study

The retained `/tmp` directories for the historical Java/React study had been emptied. An initial Claude attempt was recorded as an **infrastructure failure with zero candidate execution**. The reusable historical preparation now rejects missing JARs or frontend builds before freezing a study; [the integrity test](../history-study/test_integrity.py) covers that failure. We subsequently rebuilt the pinned native revisions and completed a separate [six-run Opus 5.5 historical cart diagnostic](2026-09-24-history-opus55-diagnostic.md). Its prespecified seeded result was 0/2 in all three arms; all six found a related direct-update defect. The incomplete September 12 historical result remains ungraded and unchanged.

A meaningful effectiveness claim needs independently curated, previously unseen tasks with room below the baseline ceiling, corrected controls, balanced repetitions and a frozen primary outcome. The API audit score here is suitable as one behavior measure, but a future study must also review whether each observed fault became an actionable report and whether controls drew unsupported claims. Do not select or revise cases after seeing treatment outcomes to make a preferred arm win.
