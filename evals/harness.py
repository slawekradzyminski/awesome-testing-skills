#!/usr/bin/env python3
"""Prepare isolated agent tasks and validate evidence; semantic grading stays explicit."""

import argparse
import hashlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
CHILDREN = {}
BENCHMARK_SCOPE = {"version": 1, "included": ["application-behavior", "practical-testing-outcomes"],
                   "excluded": ["documentation-only-defects"]}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file()
            and "__pycache__" not in p.parts and not p.name.endswith(".pyc")}


def mutate(directory, variant):
    edits = {
        "quantity": ("domain.py", "if type(quantity) is not int or quantity < 0:",
                     "if type(quantity) is not int:"),
        "length-message": ("domain.py", 'f"{field} length must be between 4 and 255 characters"',
                           'f"Minimum {field} length: 4 characters"'),
        "password-bytes": ("domain.py", "MAX_ENCODED_PASSWORD_BYTES = 1020", "MAX_ENCODED_PASSWORD_BYTES = 72"),
        "cancel": ("static/index.html", '<button id="cancel" type="button">', '<button id="cancel">'),
        "order-ownership": ("app.py", 'if order["owner"] != actor:', 'if False:'),
        "profile-cancel": ("static/index.html", '<button id="cancel" type="button" disabled>', '<button id="cancel" disabled>'),
    }
    if variant == "control":
        return
    filename, old, new = edits[variant]
    path = directory / filename
    original = path.read_text()
    if original.count(old) != 1:
        raise ValueError(f"Mutation anchor changed: {filename}")
    path.write_text(original.replace(old, new))


REPORTING = """# Evaluation output contract

## Benchmark scope

Evaluate application behavior and practical testing outcomes. Documentation-only
defects are excluded: do not audit README text, OpenAPI descriptions, or response
schema documentation. Use requirements/contracts as context, but a finding must
demonstrate incorrect application behavior, not merely an incorrect description.
If the requirement itself is uncertain, report that limitation rather than invent
a functional defect. Incorrect runtime validation feedback and rejection of valid
input remain in scope. Do not count documentation-only observations as findings.

## Deliverables

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
"""


def create_run(out):
    run = Path(out).resolve()
    # Never overwrite a prior evaluation, source checkout, or a caller's files.
    run.mkdir(parents=True, exist_ok=False)
    (run / "candidate").mkdir()
    (run / "controller").mkdir()
    (run / "candidate/evidence").mkdir()
    return run


def copy_skill(candidate, name, enabled):
    if not enabled:
        return "Perform exploratory testing using your normal approach."
    destination = candidate / "skills" / name
    shutil.copytree(ROOT / "skills" / name, destination)
    return f"Use ${name} from {destination / 'SKILL.md'}."


def start_fixture(run, unavailable=False):
    run = Path(run).resolve()
    control = run / "controller"
    app = run / "candidate/app"
    if not app.exists():
        app = control / "runtime-app"
    entrypoint = app / "app.py"
    if unavailable:
        entrypoint = control / "unavailable.py"
        shutil.copy2(EVALS / "fixtures/unavailable.py", entrypoint)
    with (control / "server.log").open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(entrypoint), "--ready", str(control / "ready.json"),
             "--audit", str(control / "audit.jsonl")], cwd=app, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
    CHILDREN[process.pid] = process
    for _ in range(100):
        if (control / "ready.json").exists():
            return read_json(control / "ready.json")["base_url"]
        if process.poll() is not None:
            raise RuntimeError(f"Fixture failed; inspect {control / 'server.log'}")
        time.sleep(0.05)
    process.terminate()
    process.wait(timeout=5)
    raise RuntimeError("Fixture startup timed out")


def prepare(case_id, out, without_skill=False):
    case = next(c for c in read_json(EVALS / "cases.json")["cases"] if c["id"] == case_id)
    run = create_run(out)
    candidate, control = run / "candidate", run / "controller"
    app = control / "runtime-app" if case["access"] == "runtime-only" else candidate / "app"
    shutil.copytree(EVALS / case.get("fixture", "sample-app"), app, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    mutate(app, case["variant"])
    shutil.copy2(app / "requirements.md", candidate / "requirements.md")
    invocation = copy_skill(candidate, case["skill"], not without_skill)
    base_url = None if case["access"] == "source-only" else start_fixture(run, case.get("environment") == "unavailable")
    source = "Application source is app/. Inspect its relevant code and existing tests." if case["access"] != "runtime-only" else "Source code cannot be shared for this session. Continue with runtime exploration."
    runtime = f"Runtime: {base_url}." if base_url else "The runtime is unavailable. Do not start it; perform a source-only assessment and propose reproductions."
    scope = "Explore the existing cart quantity-update API and its product data." if case["skill"].startswith("api") else "Explore the cart editor, its visible totals, and the Save/Cancel interaction. Use Playwright CLI or an available browser agent."
    permissions = "Use Alice/Bob's disposable fixture identities documented in the requirements. You may update only this isolated fixture's carts and restore your changes where possible."
    if case.get("fixture") == "course-app":
        scope = ("Explore sign-in request validation and corrective feedback." if case["feature"] == "signin"
                 else "Explore registration input validation, persistence and cleanup.")
        permissions = "Use only synthetic URL-safe usernames, .test emails and invented passwords. You may create, inspect and delete your own disposable registrations. Production authentication is outside this fixture's scope."
    if case.get("fixture") == "validation-app":
        scope = ("Explore order retrieval and access boundaries using the documented disposable identities."
                 if case["feature"] == "orders" else
                 "Explore the profile editor, Save/Cancel interaction, and persisted display name. Use Playwright CLI or an available browser agent.")
        permissions = ("Read only the two fixture orders with its synthetic identities; no order mutations are supported."
                       if case["feature"] == "orders" else
                       "You may edit this isolated fixture's scratch profile. Restore the display name where possible and report the remaining save count.")
    prompt = f"""{invocation}

{scope}
{source}
{runtime}
Read requirements.md and REPORTING.md. Assess the feature and report the outcome supported by evidence.
{permissions}
If access fails, make at most six availability requests in total, then explain what could and could not be tested.
Do not start or repair an unavailable service; its lifecycle belongs to the fixture owner.
Spend at most five minutes and 60 API requests (UI work: at most 45 browser actions).
Stay within the described feature scope; report limitations and do not invent defects.
All work and deliverables belong in {candidate}.
"""
    (candidate / "TASK.md").write_text(prompt)
    (candidate / "REPORTING.md").write_text(REPORTING)
    write_json(control / "manifest.json", {"case": case, "reporting_version": 2, "benchmark_scope": BENCHMARK_SCOPE, "with_skill": not without_skill,
               "base_url": base_url, "app_path": str(app), "app_hashes": hashes(app),
               "skill_hashes": hashes(candidate / "skills") if not without_skill else {},
               "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()})
    print(json.dumps({"run": str(run), "candidate": str(candidate), "task": str(candidate / "TASK.md")}))


def snapshot_repo(source, destination):
    """Copy tracked committed files, never local modifications or .git history."""
    source = Path(source).resolve()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    data = subprocess.check_output(["git", "archive", "--format=tar", revision], cwd=source)
    destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if member.isfile() and not path.is_absolute() and ".." not in path.parts:
                # Runtime configuration and datasets are not needed for code inspection.
                if path.name.startswith(".env") or path.suffix.lower() in (".pem", ".key", ".p12"):
                    continue
                if any(part in (".git", "node_modules", "artifacts", "reports") for part in path.parts):
                    continue
                target = destination / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    return {"revision": revision, "working_tree_changes_excluded": True, "hashes": hashes(destination)}


def prepare_live(profile_id, out, sources=None, without_skill=False):
    profiles = read_json(EVALS / "profiles.json")
    profile = profiles[profile_id]
    run = create_run(out)
    candidate, control = run / "candidate", run / "controller"
    invocation = copy_skill(candidate, profile["skill"], not without_skill)
    provenance = {}
    for name, source in (sources or {}).items():
        if source:
            (candidate / "source").mkdir(exist_ok=True)
            provenance[name] = snapshot_repo(source, candidate / "source" / name)
    has_source = bool(provenance)
    if has_source:
        write_json(candidate / "source-revisions.json", {
            name: {"revision": source["revision"], "deployed_match": "unverified"}
            for name, source in provenance.items()})
    allowed = ["/login", "/v3/api-docs", "/api/v1/products", "/api/v1/cart"]
    prompt = f"""{invocation}

Explore Awesome LocalStack's public {'API behavior and authentication boundary' if profile['surface'] == 'api' else 'login interface and its public navigation'} at {profile['base_url']}.
This is an optional real-stack evaluation, with no known bug list. No findings is a valid outcome.
{'Source snapshots are under source/. Read source-revisions.json for their committed revisions; deployment correspondence is unverified.' if has_source else 'Source cannot be shared in this run. Proceed with black-box observations and identify limits.'}
Use available requirements/contracts; distinguish inferred expectations from documented facts.

The run is PUBLIC READ-ONLY. Do not sign in, submit forms (including login/reset), create accounts,
send email, change data, inject faults, or enumerate private records. Do not use stored credentials.
For direct HTTP probes, only GET requests to {', '.join(allowed)} are in scope, at most 12 requests.
For browser work, use a fresh session and public pages/assets only; passive scripts may fetch public data.
You may inspect labels, focus, responsive layout, validation attributes and network observations,
but do not press submit or interact with actions that send mutations. At most 30 browser actions.
Spend at most five minutes. Report important gaps that would require an authorized disposable session.
Keep all deliverables in {candidate}. Read REPORTING.md. No product/source changes or external issues.
"""
    (candidate / "TASK.md").write_text(prompt)
    (candidate / "REPORTING.md").write_text(REPORTING)
    write_json(control / "manifest.json", {"type": "live", "reporting_version": 2, "benchmark_scope": BENCHMARK_SCOPE, "profile": profile_id,
               "case": {"id": profile_id, "access": "source-runtime" if has_source else "runtime-only", "expected_requirements": []},
               "with_skill": not without_skill, "base_url": profile["base_url"], "source_provenance": provenance,
               "source_revisions_supplied": has_source,
               "skill_hashes": hashes(candidate / "skills") if not without_skill else {}})
    print(json.dumps({"run": str(run), "task": str(candidate / "TASK.md")}))


def preflight(profile_id):
    profile = read_json(EVALS / "profiles.json")[profile_id]
    results = []
    for path in ("/login", "/v3/api-docs"):
        try:
            request = Request(profile["base_url"] + path,
                              headers={"User-Agent": "exploratory-testing-skills/1.0 (+public-read-only-preflight)"})
            with urlopen(request, timeout=10) as response:
                data = response.read(2_000_001)
                results.append({"path": path, "status": response.status,
                                "content_type": response.headers.get("Content-Type"),
                                "body_bytes_sampled": len(data), "complete": len(data) <= 2_000_000})
        except HTTPError as error:
            with error:
                results.append({"path": path, "status": error.code,
                                "content_type": error.headers.get("Content-Type")})
        except Exception as error:
            results.append({"path": path, "error": str(error)})
    print(json.dumps({"profile": profile_id, "public_get_only": True, "results": results}, indent=2))


def stop(run):
    control = Path(run).resolve() / "controller"
    ready_file = control / "ready.json"
    if not ready_file.exists():
        return
    pid = read_json(ready_file)["pid"]
    command = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
    if command.returncode == 0 and str(control / "ready.json") in command.stdout:
        os.kill(pid, signal.SIGTERM)
        child = CHILDREN.pop(pid, None)
        if child:
            child.wait(timeout=5)
        print(f"Stopped owned fixture {pid}")
    else:
        print("Fixture is no longer running; no unrelated process was stopped")


def valid_evidence(candidate, value):
    candidate = Path(candidate).resolve()
    if not isinstance(value, str) or not value:
        return False
    p = (candidate / value).resolve()
    return not Path(value).is_absolute() and p.is_relative_to(candidate) and p.is_file() and p.stat().st_size > 0


def matching_observation(observation, record):
    # The fixture logs a parsed route path, not the query string. Candidate request
    # evidence still needs manual review for query/header/body-specific claims.
    path = observation.get("path")
    return (isinstance(path, str) and path.startswith("/") and
            urlsplit(path).path == record["path"] and
            all(observation.get(key) == record[key] for key in ("method", "status")))



def check_outcomes(report, case):
    errors = []
    status = report.get("runtime_status")
    if status not in ("tested", "blocked", "not-run"):
        errors.append("Missing or invalid runtime_status")
    if (status == "tested") != report.get("runtime_exercised"):
        errors.append("Runtime status contradicts runtime_exercised")
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        return errors + ["Missing explicit check outcomes"]
    for check in checks:
        if not isinstance(check, dict):
            errors.append("Check outcomes must be objects")
            continue
        if not all(isinstance(check.get(k), str) and check[k].strip() for k in ("name", "expected", "actual")):
            errors.append("Check missing name, expected or actual")
        if check.get("basis") not in ("runtime", "source") or check.get("status") not in ("passed", "failed", "blocked", "not-run"):
            errors.append("Unknown check basis or outcome")
        if not isinstance(check.get("evidence"), list) or (check.get("status") != "not-run" and not check.get("evidence")):
            errors.append("Check outcome requires evidence")
        if check.get("basis") == "source" and case["access"] == "runtime-only":
            errors.append("Source check claimed without source access")
        if check.get("basis") == "runtime" and check.get("status") in ("passed", "failed") and status != "tested":
            errors.append("Functional runtime check claimed without tested runtime")
    return errors


def grade(run):
    run = Path(run).resolve()
    candidate, control = run / "candidate", run / "controller"
    manifest = read_json(control / "manifest.json")
    report = read_json(candidate / "submission.json")
    errors = []
    for field in ("findings", "risks", "observations", "limitations"):
        if not isinstance(report.get(field), list):
            errors.append(f"{field} must be an array")
    if errors:
        raise ValueError("; ".join(errors))
    for field in ("findings", "risks", "observations"):
        if any(not isinstance(item, dict) for item in report[field]):
            raise ValueError(f"{field} entries must be objects")
    if any(not isinstance(item.get("evidence"), list) for item in report["findings"]):
        raise ValueError("Finding evidence must be an array of relative paths")
    for field in ("source_access", "runtime_exercised"):
        if type(report.get(field)) is not bool:
            errors.append(f"{field} must be a boolean")
    if not isinstance(report.get("cleanup"), str) or not report["cleanup"].strip():
        errors.append("Missing cleanup statement")
    if not (candidate / "report.md").is_file():
        errors.append("Missing narrative report")
    if not report["risks"]:
        errors.append("No risk assessment supplied")
    for item in report["findings"]:
        for field in ("requirement_id", "title", "status", "expected", "actual", "impact", "evidence"):
            if not item.get(field):
                errors.append(f"Finding missing {field}")
        if item.get("status") not in ("confirmed", "code-evidenced", "suspected"):
            errors.append("Unknown finding evidence state")
        for evidence in item.get("evidence", []):
            if not valid_evidence(candidate, evidence):
                errors.append(f"Missing or out-of-scope finding evidence: {evidence}")
    for item in report["observations"]:
        if not valid_evidence(candidate, item.get("evidence")):
            errors.append("Missing or out-of-scope observation evidence")
    for check in report.get("checks", []) if isinstance(report.get("checks"), list) else []:
        if isinstance(check, dict) and isinstance(check.get("evidence"), list):
            for evidence in check["evidence"]:
                if not valid_evidence(candidate, evidence):
                    errors.append("Missing or out-of-scope check evidence")
    for risk in report["risks"]:
        if not all(risk.get(k) for k in ("area", "reason", "priority", "next_probe")):
            errors.append("Incomplete risk assessment entry")
    case = manifest["case"]
    if report.get("source_access") != (case["access"] != "runtime-only"):
        errors.append("Source-access claim contradicts prepared access")
    audit_path = control / "audit.jsonl"
    audit = [json.loads(line) for line in audit_path.read_text().splitlines()] if audit_path.exists() else []
    api_records = [row for row in audit if row["path"].startswith("/api/")]
    if case["access"] == "source-only" and (report.get("runtime_exercised") or report["observations"]):
        errors.append("Runtime execution claimed in source-only case")
    unavailable = case.get("environment") == "unavailable"
    if unavailable:
        if report.get("runtime_exercised") or report.get("runtime_status") != "blocked":
            errors.append("Unavailable runtime must be reported as blocked, not functionally tested")
        if not audit or any(row["status"] != 503 for row in audit):
            errors.append("Missing expected unavailable-service evidence")
        if len(audit) > 6:
            errors.append("Availability attempts exceeded bounded retry budget (6)")
    if manifest.get("reporting_version", 1) >= 2:
        errors.extend(check_outcomes(report, case))
    live = manifest.get("type") == "live"
    if not live and not unavailable and case["access"] != "source-only" and (not report.get("runtime_exercised") or not api_records):
        errors.append("Missing runtime exploration")
    if len(api_records) > 60:
        errors.append("API request budget exceeded")
    for observation in ([] if live else report["observations"]):
        if not any(matching_observation(observation, row) for row in audit):
            errors.append(f"Observation has no matching server record: {observation.get('path')}")
    if not live and hashes(Path(manifest["app_path"])) != manifest["app_hashes"]:
        errors.append("Application or requirements were modified")
    for name, source in manifest.get("source_provenance", {}).items():
        if hashes(candidate / "source" / name) != source["hashes"]:
            errors.append(f"Source snapshot changed: {name}")
    if manifest.get("source_revisions_supplied"):
        expected_revisions = {name: {"revision": source["revision"], "deployed_match": "unverified"}
                              for name, source in manifest["source_provenance"].items()}
        revision_file = candidate / "source-revisions.json"
        if not revision_file.is_file() or read_json(revision_file) != expected_revisions:
            errors.append("Source revision metadata changed or removed")
    if manifest["with_skill"] and hashes(candidate / "skills") != manifest["skill_hashes"]:
        errors.append("Skill snapshot was modified")
    expected = set(case["expected_requirements"])
    claimed = {f["requirement_id"] for f in report["findings"] if isinstance(f.get("requirement_id"), str)
               and f.get("status") in ("confirmed", "code-evidenced")}
    # This signature establishes API behavior, not whether the report explains it correctly.
    negative_write = any(r["method"] == "PUT" and r["status"] == 200 and
                         isinstance(r.get("request"), dict) and type(r["request"].get("quantity")) is int and
                         r["request"]["quantity"] < 0 for r in audit)
    negative_read = any(r["method"] == "GET" and r["path"] == "/api/v1/cart" and
                        isinstance(r.get("response"), dict) and r["response"].get("totalItems", 0) < 0 for r in audit)
    result = {"case": case["id"], "with_skill": manifest["with_skill"],
              "artifact_checks_passed": not errors, "errors": errors,
              "expected_requirements_reported": sorted(expected & claimed),
              "expected_requirements_missing": sorted(expected - claimed),
              "additional_claims_for_review": sorted(claimed - expected),
              "api_requests": None if live else len(api_records), "negative_quantity_write_and_read_observed": negative_write and negative_read,
              "query_observations_requiring_manual_review": [o["path"] for o in report["observations"]
                  if isinstance(o.get("path"), str) and urlsplit(o["path"]).query],
              "semantic_review": "REQUIRED: evaluate report correctness, UI action causality, severity, risk quality, and false positives using rubric.md. This is not an automatic skill pass."}
    if "benchmark_scope" in manifest:
        result["benchmark_scope"] = manifest["benchmark_scope"]
        result["semantic_review"] += " Apply the recorded benchmark scope: exclude documentation-only claims from discovery credit; review scope adherence separately."
    write_json(control / "grade.json", result)
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("case")
    prepare_parser.add_argument("--out", required=True)
    prepare_parser.add_argument("--without-skill", action="store_true")
    live_parser = sub.add_parser("prepare-live")
    live_parser.add_argument("profile", choices=read_json(EVALS / "profiles.json"))
    live_parser.add_argument("--out", required=True)
    live_parser.add_argument("--backend")
    live_parser.add_argument("--frontend")
    live_parser.add_argument("--stack")
    live_parser.add_argument("--without-skill", action="store_true")
    sub.add_parser("preflight").add_argument("profile", choices=read_json(EVALS / "profiles.json"))
    for command in ("stop", "grade"):
        sub.add_parser(command).add_argument("run")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.case, args.out, args.without_skill)
    elif args.command == "prepare-live":
        prepare_live(args.profile, args.out, {k: getattr(args, k) for k in ("backend", "frontend", "stack")}, args.without_skill)
    elif args.command == "preflight":
        preflight(args.profile)
    elif args.command == "stop":
        stop(args.run)
    else:
        result = grade(args.run)
        if not result["artifact_checks_passed"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
