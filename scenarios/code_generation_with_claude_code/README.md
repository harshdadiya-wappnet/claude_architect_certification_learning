# Expense Tracker

A small Python CLI for recording and summarising personal expenses. Data is stored locally in `data/expenses.json`.

This project is also a practice sandbox for **Claude Code workflows** (CLAUDE.md, slash commands, skills, plan mode vs direct execution) for the Claude certification exam, Scenario 2: *Code Generation with Claude Code*.

## Requirements

- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the `expenses` command and pytest.

## Usage

```bash
expenses add 12.50 food -d "lunch"
expenses add 40 transport --date 2026-11-20
expenses list
expenses list -c food
expenses summary
expenses delete 1
```

Without installing, run it as a module:

```bash
PYTHONPATH=src python3 -m expense_tracker.cli summary
```

Categories: `food`, `transport`, `rent`, `utilities`, `entertainment`, `other`.

## Testing

```bash
pytest
```

## Project layout

```
src/expense_tracker/
  models.py    Expense dataclass and allowed categories
  storage.py   JSON file persistence
  service.py   Business logic and validation
  cli.py       argparse entry point
tests/         pytest tests (temp-file fixture)
data/          Local expense data (git-ignored)
```

## Status

Implemented: add, list, delete, per-category totals.

Not yet implemented (stubs in `service.py`):
- `monthly_summary(year, month)`
- `export_csv(path)`
- `update(expense_id, **fields)`

These are intentionally left as exercises for practising code generation, refactoring, debugging and documentation with Claude Code.
