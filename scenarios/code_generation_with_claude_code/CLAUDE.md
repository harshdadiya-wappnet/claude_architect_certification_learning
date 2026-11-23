# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e ".[dev]"                 # install the `expenses` CLI + pytest (use a venv)
pytest                                  # run all tests
pytest tests/test_service.py::test_add_assigns_incrementing_ids   # single test
PYTHONPATH=src python3 -m expense_tracker.cli summary             # run without installing
```

No linter or formatter is configured. Python 3.10+ (code uses `X | None` syntax). No runtime dependencies.

## Architecture

Three layers under `src/expense_tracker/`, each depending only on the one below:

- `cli.py` — argparse subcommands (`add`, `list`, `delete`, `summary`). `main()` builds an `ExpenseService(JsonStorage())`, catches `ValueError` from the service, prints `Error: ...` and returns exit code 1.
- `service.py` — `ExpenseService`: all business logic and validation (positive amount, category must be in `CATEGORIES`). Raise `ValueError` for invalid input; the CLI relies on this to report errors.
- `storage.py` — `JsonStorage`: whole-file load/save of a JSON list at `data/expenses.json` (git-ignored; created on first save). Every service operation does a full `load()` then `save()`; there is no caching.
- `models.py` — `Expense` dataclass (`date` is an ISO `YYYY-MM-DD` string, not a `date` object) and the `CATEGORIES` tuple, the single source of truth for allowed categories.

IDs are assigned as `max(existing ids) + 1`, so a deleted highest ID gets reused.

## Practice stubs

`service.py` has intentionally unimplemented methods raising `NotImplementedError`: `monthly_summary(year, month)`, `export_csv(path)`, and `update(expense_id, **fields)`. They are not wired into the CLI. The README notes these are exercises for practising Claude Code workflows (this repo is a sandbox for the Claude certification exam, Scenario 2: Code Generation with Claude Code).

## Testing

Tests in `tests/test_service.py` exercise `ExpenseService` through a `service` fixture backed by `JsonStorage(tmp_path / "expenses.json")`. Always use a temp path — never the default `data/expenses.json` — in tests. pytest is configured with `pythonpath = ["src"]`, so no install is needed to run it.
