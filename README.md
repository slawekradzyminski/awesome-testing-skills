# Exploratory Testing Skills

Two reusable agent skills for code-informed exploratory testing, adapted from Sławomir Radzymiński's September 2026 Playwright workshops.

| Skill | Purpose | Preferred runtime tool |
| --- | --- | --- |
| [api-exploratory-testing](skills/api-exploratory-testing/SKILL.md) | Inspect backend code, identify risks, probe the API, and report bugs and contract gaps | curl or another available HTTP client |
| [ui-exploratory-testing](skills/ui-exploratory-testing/SKILL.md) | Inspect application code, identify risky journeys, explore the interface, and report functional and nonfunctional findings | Playwright CLI or another available browser agent |

Both skills encourage users to supply the code being tested, then use that code to choose meaningful runtime experiments. They also work without source access and clearly distinguish a source-only assessment from live testing.

The experiment guides add practical techniques for selecting useful probes: challenge the first hypothesis, compare related results against business rules, investigate state transitions, distinguish uncertain writes from failed writes, and preserve the original failure while minimizing a reproduction. UI guidance also separates ordinary user interactions from diagnostic interventions that bypass normal controls.

Detailed guidance loads through references at the point of use. Each skill remains independently copyable, supports available tools, and avoids fixed test counts, mandatory full matrices, and extra approval steps for routine authorized work.

## Use

Clone this private repository using an account with access:

```sh
gh repo clone slawekradzyminski/exploratory-testing-skills
```

Each directory under `skills/` is self-contained. Copy the desired directory, including its `references/` and `agents/` subdirectories, into the skill location used by your agent. For the workshop's repository layout, that is `.codex/skills/` for Codex or `.claude/skills/` for Claude Code. Check for an existing directory of the same name before copying; merge deliberate changes instead of overwriting it. The `agents/openai.yaml` file provides optional Codex display metadata; the instructions themselves are ordinary Markdown.

For example, from the cloned repository, after choosing the target project and verifying that these skill names do not already exist:

```sh
mkdir -p /path/to/project/.codex/skills
cp -R skills/api-exploratory-testing /path/to/project/.codex/skills/
cp -R skills/ui-exploratory-testing /path/to/project/.codex/skills/
```

The skills use available HTTP/browser tools. They do not bundle a browser runtime or require a particular application stack. The UI skill prefers the Playwright CLI skill when it is installed and permits another browser agent when it is not.

## Example requests

```text
Use $api-exploratory-testing to explore the cart API.
Backend code: /path/to/backend, branch feature/cart-updates.
Test URL: http://localhost:8080.
Requirements: docs/cart-rules.md.
Use the two disposable customer accounts from the local test configuration.
You may create and delete your own test carts. Spend up to 20 minutes.
Identify risky areas and report reproducible bugs with HTTP evidence.
```

```text
Use $ui-exploratory-testing to explore account settings and profile editing.
Frontend: /path/to/frontend. Backend: /path/to/backend.
Test URL: http://localhost:3000. Start with the current local branches.
Use Playwright CLI, or the available browser agent if CLI is unavailable.
Use disposable test users; avoid sending real emails.
Inspect code first, prioritize risky states, and verify them in the browser.
Report findings, supporting evidence, and meaningful coverage gaps.
```

## Expected results

- A compact risk assessment grounded in source, requirements, and observations.
- Focused live experiments and reproducible, sanitized evidence.
- Findings that distinguish observed failures, code evidence, hypotheses, and ambiguous requirements.
- Explicit limits: build mismatch, missing source/runtime, untested states, and cleanup still needed.
- Suggested regression coverage at a suitable test level.

Exploration does not automatically include product fixes, a new regression suite, external issue filing, or publication. Those actions can be included in the user's task explicitly. Routine authorized testing continues without repeated approval requests.

## Workshop lineage

Reviewed against the latest remote branch tips on September 12, 2026:

- [`hyr21` at `94dccc853d421746956ea2691ed5c4fcaa81bf95`](https://github.com/slawekradzyminski/playwright-2026/tree/94dccc853d421746956ea2691ed5c4fcaa81bf95/.codex/skills): API/UI exploration, evidence, impact assessment, visual and network review.
- [`obi25` at `db0d9393bd11816f59c44f153c56b5474a71acdf`](https://github.com/slawekradzyminski/playwright-2026/tree/db0d9393bd11816f59c44f153c56b5474a71acdf/.claude/skills): backend assessment, actual test-assertion inspection, and test-level selection.

These are generic derivatives. They remove workshop-specific hosts, credentials, directory conventions, fixed viewport policies, automation rules, and duplicate Codex/Claude copies. They retain adaptive exploration and evidence standards, add explicit source intake and risk maps, and support alternative tools and partial access.

See [validation notes](docs/validation.md) for checks and their limits.
