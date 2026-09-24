#!/usr/bin/env python3
"""Known-answer infrastructure checks, separate from agent-effectiveness results."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import study


def check(out):
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for surface in ('api', 'ui'):
        for variant in ('control', 'defects'):
            folder = out / f'{surface}-{variant}'
            folder.mkdir()
            shutil.copytree(study.HERE / 'app', folder / 'app', ignore=shutil.ignore_patterns('__pycache__'))
            if variant == 'defects':
                study.mutate(folder / 'app', surface)
            server, base = study.start_server(folder / 'app', folder)
            log, calls = [], []
            session = 'journey-check-' + surface + '-' + variant

            def request(path, body=None):
                req = Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                              headers={'X-Test-User': 'alice', 'Content-Type': 'application/json'})
                try:
                    response = urlopen(req, timeout=4)
                except HTTPError as error:
                    response = error
                with response:
                    status, value = response.status, json.load(response)
                calls.append({'path': path, 'body': body, 'status': status, 'response': value})
                return status, value

            def cli(*args):
                result = subprocess.run(['playwright-cli', '-s='+session, *args], cwd=folder,
                                        capture_output=True, text=True, timeout=45)
                log.append({'args': args, 'stdout': result.stdout, 'stderr': result.stderr})
                if result.returncode or '### Error' in result.stdout:
                    raise RuntimeError(result.stdout + result.stderr)
                return result.stdout

            try:
                bad = variant == 'defects'
                if surface == 'api':
                    assert request('/api/orders/A100/refund', {'amount': 6000})[0] == 200
                    assert request('/api/orders/A100/refund', {'amount': 5000})[0] == (200 if bad else 409)
                    assert request('/api/orders/A100')[1]['refunded'] == (11000 if bad else 6000)
                    assert request('/api/orders/A100/address', {'address': 'Newer', 'version': 1})[0] == 200
                    assert request('/api/orders/A100/address', {'address': 'Stale', 'version': 1})[0] == (200 if bad else 409)
                    assert request('/api/orders/A100')[1]['address'] == ('Stale' if bad else 'Newer')
                    assert request('/api/services', {'ids': ['A100', 'B100'], 'service': 'express'})[0] == 403
                    assert request('/api/orders/A100')[1]['service'] == ('express' if bad else 'standard')
                else:
                    cli('open', base)
                    expected = 'A100' if bad else 'A200'
                    # Standard select interactions; wait for the known delayed request to finish.
                    code = '''async page => {
                      await page.waitForFunction(() => document.getElementById('loading').textContent === '');
                      await page.locator('#order').selectOption('A200');
                      await page.waitForFunction(() => document.getElementById('heading').textContent === 'Order A200');
                      const delayed = page.waitForResponse(r => r.url().endsWith('/api/orders/A100'));
                      await page.locator('#order').selectOption('A100');
                      await page.locator('#order').selectOption('A200');
                      await delayed; await page.waitForLoadState('networkidle');
                      const actual = await page.locator('#heading').textContent();
                      if (actual !== 'Order EXPECTED') throw new Error(actual);
                      await page.locator('#save').click();
                      await page.getByText('Delivery instruction saved', {exact:true}).waitFor();
                    }'''.replace('EXPECTED', expected)
                    cli('run-code', code)
                    assert request('/api/orders/A200')[1]['note'] == ('Leave with reception' if bad else 'Ring twice')
                    cli('screenshot', '--filename=stale-order.png')
                    cli('fill', '#note', 'LOCKER: 7')
                    cli('click', '#save')
                    feedback = 'Delivery instruction saved' if bad else 'Locker delivery is unavailable; enter another instruction'
                    cli('run-code', 'async page => { await page.waitForLoadState("networkidle"); if (await page.locator("#feedback").textContent() !== '+json.dumps(feedback)+') throw new Error("feedback"); }')
                    assert request('/api/orders/A200')[1]['note'] != 'LOCKER: 7'
                    cli('screenshot', '--filename=rejected-note.png')
                    # Focus by clicking an ordinary input, then only Tab navigation.
                    cli('click', '#note')
                    cli('press', 'Tab')
                    cli('press', 'Tab')
                    focused = 'standard' if bad else 'express'
                    cli('run-code', 'async page => { if (await page.evaluate(() => document.activeElement.id) !== '+json.dumps(focused)+') throw new Error("focus"); }')
                    cli('click', '#express')
                    cli('run-code', 'async page => { await page.waitForFunction(() => document.getElementById("service").textContent === "express"); }')
                    assert request('/api/orders/A200')[1]['service'] == 'express'
                results.append({'surface': surface, 'variant': variant, 'seeds_checked': 3, 'passed': True})
            finally:
                server.terminate(); server.wait(timeout=5)
                if surface == 'ui':
                    subprocess.run(['playwright-cli', '-s='+session, 'close'], cwd=folder, capture_output=True, timeout=20)
                study.write_json(folder / 'browser-commands.json', log)
                study.write_json(folder / 'http-checks.json', calls)
    study.write_json(out / 'results.json', results)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    check(parser.parse_args().out.resolve())
