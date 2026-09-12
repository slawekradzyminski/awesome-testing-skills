#!/usr/bin/env python3
"""Verify the UI mutation/control using real clicks; not an agent evaluation."""

import argparse
import json
import subprocess
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

import harness


def check(case, out):
    harness.prepare(case, out)
    run = Path(out).resolve()
    base = harness.read_json(run / "controller/manifest.json")["base_url"]
    session = "fixture-" + uuid.uuid4().hex[:12]
    log = []

    def cli(*args):
        result = subprocess.run(["playwright-cli", f"-s={session}", *args],
                                cwd=run, text=True, capture_output=True, timeout=45)
        log.append({"args": args, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode or "### Error" in result.stdout:
            raise RuntimeError(result.stdout + result.stderr)

    def read_cart():
        with urlopen(Request(base + "/api/v1/cart", headers={"Authorization": "Bearer demo-alice"}), timeout=3) as response:
            return json.load(response)

    def wait_summary(quantity):
        cli("run-code", "async page => { await page.getByText(" +
            json.dumps(f"Quantity: {quantity} · Total: {quantity * 12}") +
            ", {exact: true}).waitFor(); }")

    try:
        cli("open", base)
        cli("resize", "1280", "720")
        wait_summary(1)
        cli("click", "getByRole('button', {name: 'Edit quantity', exact: true})")
        cli("fill", "getByRole('spinbutton', {name: 'Quantity', exact: true})", "3")
        cli("click", "getByRole('button', {name: 'Cancel', exact: true})")
        expected = 3 if case == "ui-01" else 1
        wait_summary(expected)
        after_cancel = read_cart()
        assert after_cancel["totalItems"] == expected, after_cancel
        records = [json.loads(row) for row in (run / "controller/audit.jsonl").read_text().splitlines()]
        cancel_puts = [row for row in records if row["method"] == "PUT"]
        assert len(cancel_puts) == (1 if case == "ui-01" else 0), cancel_puts
        cli("screenshot", "--filename=cancel.png")
        cli("click", "getByRole('button', {name: 'Edit quantity', exact: true})")
        cli("fill", "getByRole('spinbutton', {name: 'Quantity', exact: true})", "2")
        cli("click", "getByRole('button', {name: 'Save', exact: true})")
        wait_summary(2)
        assert read_cart()["totalItems"] == 2
        cli("reload")
        wait_summary(2)
        cli("console")
        result = {"case": case, "kind": "fixture-validation", "passed": True,
                  "quantity_after_cancel": expected, "cancel_put_requests": len(cancel_puts),
                  "quantity_after_save_and_reload": 2, "viewport": [1280, 720]}
        harness.write_json(run / "fixture-result.json", result)
        return result
    finally:
        try:
            cli("close")
        finally:
            harness.write_json(run / "browser-commands.json", log)
            harness.stop(run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Fresh output directory")
    args = parser.parse_args()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = [check(case, output / case) for case in ("ui-01", "ui-02")]
    harness.write_json(output / "results.json", results)
    print(json.dumps(results, indent=2))
