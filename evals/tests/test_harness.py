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
                "source_access": True, "runtime_exercised": False,
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
