"""Infrastructure tests; these are not agent/skill quality scores."""

import json
import tempfile
import subprocess
import contextlib
import io
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import sys
EVALS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EVALS))
import harness


def request(base, method="GET", quantity=None):
    data = json.dumps({"quantity": quantity}).encode() if method == "PUT" else None
    path = "/api/v1/cart/items/1" if method == "PUT" else "/api/v1/cart"
    req = Request(base + path, data=data, method=method,
                  headers={"Authorization": "Bearer demo-alice", "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=3) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        with error:
            return error.code, json.load(error)


class HarnessTests(unittest.TestCase):
    def test_documentation_exclusion_is_shared_by_both_conditions_and_live_tasks(self):
        with tempfile.TemporaryDirectory() as folder:
            for profile in (None, "localstack-hosted-api", "localstack-hosted-ui"):
                contracts = []
                for baseline in (False, True):
                    run = Path(folder) / f"{profile}-{baseline}"
                    if profile:
                        harness.prepare_live(profile, run, without_skill=baseline)
                    else:
                        harness.prepare("api-03", run, without_skill=baseline)
                    manifest = harness.read_json(run / "controller/manifest.json")
                    self.assertEqual(manifest["benchmark_scope"]["excluded"], ["documentation-only-defects"])
                    contract = (run / "candidate/REPORTING.md").read_text()
                    self.assertIn("Do not count documentation-only observations as findings", contract)
                    self.assertIn("Incorrect runtime validation feedback", contract)
                    self.assertIn("REPORTING.md", (run / "candidate/TASK.md").read_text())
                    contracts.append(contract)
                self.assertEqual(contracts[0], contracts[1])

    def test_unavailable_runtime_requires_honest_blocked_outcome(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder) / "run"
            harness.prepare("api-05", run)
            candidate = run / "candidate"
            manifest = harness.read_json(run / "controller/manifest.json")
            try:
                status, payload = request(manifest["base_url"])
                self.assertEqual(status, 503)
                (candidate / "report.md").write_text("Application blocked by 503. Functional cart tests not run.")
                (candidate / "evidence/http.txt").write_text(json.dumps({"status": status, "body": payload}))
                report = {"source_access": True, "runtime_exercised": False, "runtime_status": "blocked",
                    "checks": [{"name": "Read cart", "basis": "runtime", "status": "blocked", "expected": "Cart response",
                        "actual": "503 gateway response", "evidence": ["evidence/http.txt"]}],
                    "findings": [], "risks": [{"area": "cart", "reason": "Cannot reach application", "priority": "high", "next_probe": "Retry after service restored"}],
                    "observations": [{"method": "GET", "path": "/api/v1/cart", "status": 503, "action": "Availability check", "evidence": "evidence/http.txt"}],
                    "limitations": ["Functional runtime untested"], "cleanup": "No state changed"}
                harness.write_json(candidate / "submission.json", report)
                graded = harness.grade(run)
                self.assertTrue(graded["artifact_checks_passed"])
                self.assertEqual(graded["benchmark_scope"], manifest["benchmark_scope"])
                report["runtime_exercised"] = True
                report["runtime_status"] = "tested"
                report["checks"][0]["status"] = "passed"
                harness.write_json(candidate / "submission.json", report)
                result = harness.grade(run)
                self.assertFalse(result["artifact_checks_passed"])
                self.assertIn("Unavailable runtime must be reported as blocked, not functionally tested", result["errors"])
            finally:
                harness.stop(run)

    def test_runtime_only_clean_case_does_not_supply_source_or_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder) / "run"
            harness.prepare("api-04", run)
            try:
                candidate = run / "candidate"
                self.assertFalse((candidate / "app").exists())
                self.assertTrue((run / "controller/runtime-app/domain.py").exists())
                task = (candidate / "TASK.md").read_text()
                self.assertIn("Source code cannot be shared", task)
                self.assertNotIn("no-confirmed-defects", task)
                self.assertNotIn("control", task)
            finally:
                harness.stop(run)

    def test_check_outcomes_distinguish_access_and_unexecuted_work(self):
        report = {"runtime_status": "blocked", "runtime_exercised": False,
                  "checks": [{"name": "Cart check", "basis": "runtime", "status": "passed",
                              "expected": "Cart", "actual": "Claimed success", "evidence": ["http.txt"]}]}
        self.assertIn("Functional runtime check claimed without tested runtime", harness.check_outcomes(report, {"access": "source-runtime"}))
        report["checks"][0].update(basis="source", status="passed")
        self.assertIn("Source check claimed without source access", harness.check_outcomes(report, {"access": "runtime-only"}))

    def test_course_mutations_have_matching_working_controls(self):
        def send(base, method, path, body=None):
            req = Request(base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                          headers={"Content-Type": "application/json"})
            try:
                response = urlopen(req, timeout=3)
            except HTTPError as error:
                response = error
            with response:
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        with tempfile.TemporaryDirectory() as folder:
            for case in ("api-06", "api-07", "api-08", "api-09"):
                with self.subTest(case=case):
                    run = Path(folder) / case
                    harness.prepare(case, run)
                    base = harness.read_json(run / "controller/manifest.json")["base_url"]
                    try:
                        if case in ("api-06", "api-07"):
                            status, result = send(base, "POST", "/api/v1/users/signin", {"username": "x" * 256, "password": "xxxx"})
                            self.assertEqual(status, 400)
                            self.assertEqual("Minimum" in result["username"], case == "api-06")
                            self.assertEqual(send(base, "POST", "/api/v1/users/signin", {"username": "xxxx", "password": "xxxx"})[0], 422)
                        else:
                            for idx, password in enumerate(("x" * 72, "x" * 73, "ą" * 37, "🌍" * 255)):
                                name = f"synthetic-{idx}"
                                status, _ = send(base, "POST", "/api/v1/users/signup", {"username": name, "email": name + "@example.test", "password": password})
                                accepted = case == "api-09" or idx == 0
                                self.assertEqual(status, 201 if accepted else 400)
                                self.assertEqual(send(base, "GET", "/api/v1/users/" + name)[0], 200 if accepted else 404)
                                if accepted:
                                    self.assertEqual(send(base, "DELETE", "/api/v1/users/" + name)[0], 204)
                                    self.assertEqual(send(base, "GET", "/api/v1/users/" + name)[0], 404)
                    finally:
                        harness.stop(run)

    def test_query_observation_matches_parsed_audit_path_without_weakening_status_check(self):
        record = {"method": "PUT", "path": "/api/v1/cart/items/1", "status": 200}
        observation = {"method": "PUT", "path": "/api/v1/cart/items/1?username=bob", "status": 200}
        self.assertTrue(harness.matching_observation(observation, record))
        self.assertFalse(harness.matching_observation({**observation, "status": 401}, record))
        self.assertFalse(harness.matching_observation({**observation, "path": "/api/v1/cart/items/2?username=bob"}, record))
        self.assertFalse(harness.matching_observation({**observation, "method": "GET"}, record))

    def test_preflight_identifies_client_and_uses_only_public_gets(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                requests.append((self.command, self.path))
                # Reproduce the observed edge rejection of urllib's default identity.
                identified = self.headers.get("User-Agent", "").startswith("exploratory-testing-skills/")
                self.send_response(200 if identified else 403)
                self.end_headers()
                self.wfile.write(b"public response")
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            profiles = {"fixture": {"base_url": f"http://127.0.0.1:{server.server_port}"}}
            output = io.StringIO()
            with patch.object(harness, "read_json", return_value=profiles), contextlib.redirect_stdout(output):
                harness.preflight("fixture")
            result = json.loads(output.getvalue())
            self.assertEqual([row["status"] for row in result["results"]], [200, 200])
            self.assertEqual(requests, [("GET", "/login"), ("GET", "/v3/api-docs")])
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_source_assessment_integrity_passes_then_detects_modified_source(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder) / "run"
            harness.prepare("api-03", run)
            candidate = run / "candidate"
            (candidate / "report.md").write_text("Source-only assessment, runtime unavailable.")
            (candidate / "evidence/code.txt").write_text("The quantity guard checks type but not sign.")
            harness.write_json(candidate / "submission.json", {
                "source_access": True, "runtime_exercised": False, "runtime_status": "not-run",
                "checks": [{"name": "Quantity sign guard", "basis": "source", "status": "failed",
                            "expected": "Reject negatives", "actual": "Sign guard absent", "evidence": ["evidence/code.txt"]}],
                "findings": [{"requirement_id": "CART-2", "title": "Missing quantity sign guard",
                              "status": "code-evidenced", "expected": "CART-2 rejects negatives",
                              "actual": "Negative integers pass the guard", "impact": "Potential invalid totals",
                              "evidence": ["evidence/code.txt"]}],
                "risks": [{"area": "cart", "reason": "state", "priority": "high", "next_probe": "PUT then GET"}],
                "observations": [], "limitations": ["Runtime unavailable"], "cleanup": "No runtime changes"})
            result = harness.grade(run)
            self.assertTrue(result["artifact_checks_passed"])
            self.assertEqual(result["expected_requirements_reported"], ["CART-2"])
            (candidate / "app/domain.py").write_text("Modified source")
            result = harness.grade(run)
            self.assertFalse(result["artifact_checks_passed"])
            self.assertIn("Application or requirements were modified", result["errors"])

    def test_live_source_snapshot_excludes_local_edits_and_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder) / "repo"
            repo.mkdir()
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.DEVNULL)
            git("init")
            (repo / "source.py").write_text("committed\n")
            (repo / ".env").write_text("EXAMPLE=excluded\n")
            git("add", ".")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "Fixture")
            (repo / "source.py").write_text("uncommitted\n")
            (repo / "untracked.txt").write_text("local\n")
            target = Path(folder) / "snapshot"
            provenance = harness.snapshot_repo(repo, target)
            self.assertEqual((target / "source.py").read_text(), "committed\n")
            self.assertEqual((repo / "source.py").read_text(), "uncommitted\n")
            self.assertFalse((target / ".env").exists())
            self.assertFalse((target / "untracked.txt").exists())
            self.assertFalse((target / ".git").exists())
            self.assertEqual(provenance["revision"], git("rev-parse", "HEAD").strip())
            live = Path(folder) / "live-run"
            harness.prepare_live("localstack-hosted-api", live, {"backend": repo})
            supplied = harness.read_json(live / "candidate/source-revisions.json")
            self.assertEqual(supplied["backend"]["revision"], provenance["revision"])
            self.assertEqual(supplied["backend"]["deployed_match"], "unverified")

    def test_source_only_without_skill_has_no_runtime_or_skill_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder) / "run"
            harness.prepare("api-03", run, without_skill=True)
            manifest = harness.read_json(run / "controller/manifest.json")
            self.assertIsNone(manifest["base_url"])
            self.assertFalse((run / "controller/ready.json").exists())
            self.assertFalse((run / "candidate/skills").exists())
            self.assertTrue((run / "candidate/app/domain.py").is_file())

    def test_frozen_quantity_mutation_changes_runtime_contract(self):
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            for variant in ("control", "quantity"):
                app = Path(folder) / variant
                shutil.copytree(EVALS / "sample-app", app, ignore=shutil.ignore_patterns("__pycache__"))
                harness.mutate(app, variant)
                run = Path(folder) / (variant + "-run")
                (run / "candidate").mkdir(parents=True)
                (run / "controller").mkdir()
                shutil.move(str(app), str(run / "candidate/app"))
                base = harness.start_fixture(run)
                try:
                    status, result = request(base, "PUT", -1)
                    _, persisted = request(base)
                    self.assertEqual(status, 400 if variant == "control" else 200)
                    self.assertEqual(persisted["totalItems"], 1 if variant == "control" else -1)
                    # Both variants retain the ordinary valid behavior.
                    self.assertEqual(request(base, "PUT", 3)[1]["totalPrice"], 36)
                finally:
                    harness.stop(run)

    def test_mutation_fails_closed_if_source_anchor_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            app = Path(folder)
            (app / "domain.py").write_text("unrelated implementation")
            with self.assertRaises(ValueError):
                harness.mutate(app, "quantity")

    def test_evidence_cannot_escape_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            candidate = root / "candidate"
            candidate.mkdir()
            (root / "oracle.txt").write_text("private grading evidence")
            (candidate / "valid.txt").write_text("actual candidate evidence")
            (candidate / "leak.txt").symlink_to(root / "oracle.txt")
            self.assertTrue(harness.valid_evidence(candidate, "valid.txt"))
            self.assertFalse(harness.valid_evidence(candidate, "../oracle.txt"))
            self.assertFalse(harness.valid_evidence(candidate, "leak.txt"))
            self.assertFalse(harness.valid_evidence(candidate, str(candidate / "valid.txt")))

    def test_run_creation_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "run"
            harness.create_run(path)
            sentinel = path / "candidate/keep.txt"
            sentinel.write_text("original")
            with self.assertRaises(FileExistsError):
                harness.create_run(path)
            self.assertEqual(sentinel.read_text(), "original")

    def test_grader_rejects_fabricated_source_only_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            candidate = run / "candidate"
            control = run / "controller"
            candidate.mkdir()
            control.mkdir()
            app = candidate / "app"
            app.mkdir()
            (app / "source.py").write_text("pass\n")
            (candidate / "report.md").write_text("A report")
            (candidate / "evidence.txt").write_text("Claimed HTTP result")
            harness.write_json(control / "manifest.json", {
                "case": {"id": "source-only", "access": "source-only", "expected_requirements": []},
                "app_path": str(app), "app_hashes": harness.hashes(app), "with_skill": False})
            harness.write_json(candidate / "submission.json", {
                "source_access": True, "runtime_exercised": True, "findings": [],
                "risks": [{"area": "cart", "reason": "state", "priority": "high", "next_probe": "read"}],
                "observations": [{"method": "GET", "path": "/api/v1/cart", "status": 200, "evidence": "evidence.txt"}],
                "limitations": []})
            result = harness.grade(run)
            self.assertFalse(result["artifact_checks_passed"])
            self.assertIn("Runtime execution claimed in source-only case", result["errors"])


if __name__ == "__main__":
    unittest.main()
