# Computer-Use Agent CRM Demo

This example shows a controlled browser agent that operates a local CRM app with
Playwright. It is intentionally small: the point is step-level control,
traceability, and recoverable execution rather than a broad web automation claim.

## Run

Install optional dependencies and Playwright browsers:

```bash
pip install -e '.[browser,gateway]'
playwright install chromium
```

Run the deterministic demo:

```bash
python -m examples.computer_use_agent run \
  --goal "Mark this month's pending customers as followed up and export the result"
```

The command starts the local CRM demo on `127.0.0.1:8765`, signs in with the demo
account, filters `2026-05` pending customers, marks them followed up, exports CSV,
and writes a trace under `/tmp/computer-use-agent-traces`.
Browser navigation is restricted to the configured start URL origin.

To inspect the UI manually:

```bash
python -m examples.computer_use_agent serve
```

Open `http://127.0.0.1:8765`.

## Modes

- `--planner scripted`: deterministic smoke path, no model key required.
- `--planner llm`: uses the repo's existing `ModelClient` configuration and still
  restricts the model to one JSON action per step.

## Trace Artifacts

Each run writes:

- `steps.jsonl`: action, args, observation, duration, errors.
- `screenshots/`: one screenshot per step.
- `downloads/`: exported CSV files.
- `report.md`: final execution summary.
