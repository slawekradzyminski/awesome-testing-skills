"""Orders/profile fixture checks. These do not measure agent effectiveness."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness


def request(base, path, actor=None, body=None):
    headers = {"Content-Type": "application/json"}
    if actor:
        headers["X-Test-User"] = actor
    req = Request(base + path, headers=headers,
                  data=json.dumps(body).encode() if body is not None else None)
    try:
        response = urlopen(req, timeout=3)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


class ValidationAppTests(unittest.TestCase):
    def test_order_defect_and_control_keep_identity_and_not_found_contrasts(self):
        with tempfile.TemporaryDirectory() as folder:
            for case, cross_status in (("api-10", 200), ("api-11", 403)):
                run = Path(folder) / case
                harness.prepare(case, run)
                try:
                    base = harness.read_json(run / "controller/manifest.json")["base_url"]
                    for actor in (None, "unknown"):
                        self.assertEqual(request(base, "/api/orders/1", actor)[0], 401)
                    for actor, own, other in (("alice", "1", "2"), ("bob", "2", "1")):
                        status, payload = request(base, "/api/orders/" + own, actor)
                        self.assertEqual((status, payload["owner"]), (200, actor))
                        status, payload = request(base, "/api/orders/" + other, actor)
                        self.assertEqual(status, cross_status)
                        if status == 200:
                            self.assertNotEqual(payload["owner"], actor)
                        else:
                            self.assertNotIn("item", payload)
                        self.assertEqual(request(base, "/api/orders/999", actor)[0], 404)
                    audit = [json.loads(line) for line in (run / "controller/audit.jsonl").read_text().splitlines()]
                    self.assertTrue(any(row["actor"] == "alice" and row["path"] == "/api/orders/2" and row["status"] == cross_status for row in audit))
                finally:
                    harness.stop(run)

    def test_profile_writes_validate_input_and_reset_between_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            for case in ("ui-06", "ui-07"):
                run = Path(folder) / case
                harness.prepare(case, run)
                try:
                    base = harness.read_json(run / "controller/manifest.json")["base_url"]
                    self.assertEqual(request(base, "/api/profile")[1], {"displayName": "Original", "saveCount": 0})
                    self.assertEqual(request(base, "/api/profile", body={"displayName": "Saved baseline"})[0], 200)
                    for body in ({}, [], {"displayName": ""}, {"displayName": 7}, {"displayName": "x" * 81}):
                        self.assertEqual(request(base, "/api/profile", body=body)[0], 400)
                    self.assertEqual(request(base, "/api/profile")[1], {"displayName": "Saved baseline", "saveCount": 1})
                    self.assertEqual(request(base, "/api/profile", body={"displayName": "Original"})[1], {"displayName": "Original", "saveCount": 2})
                finally:
                    harness.stop(run)


if __name__ == "__main__":
    unittest.main()
