# Claude API Learning

Hands-on practice for the **Claude certification exam**: the Messages API, the Claude Agent SDK, Model Context Protocol (MCP) and Claude Code workflows.

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"        # or: pip install -r requirements.txt
cp .env.example .env           # then set ANTHROPIC_API_KEY
```

`.env` is git-ignored. Never commit your API key.

## Contents

| Path | What it is |
|---|---|
| `main.py` | Async streaming chat loop with conversation history (run: `python main.py`) |
| `003_caching.ipynb` | Prompt caching notebook |
| `examples/` | Small API demos: simple chat, tool use, structured output (plain and streaming), Bedrock |
| `cli_project_COMPLETE/` | Complete CLI chat project with an MCP server and client (has its own README) |
| `my_mcp_app/` | MCP app with a TypeScript/Vite UI (has its own README; needs `npm install`) |
| `scenarios/` | One folder per exam scenario (see below) |
| `.claude/` | Claude Code commands, hooks and settings for this workspace |

## Exam scenarios

The exam presents 4 scenarios drawn at random from these 6.

| # | Scenario | Primary domains | Folder |
|---|---|---|---|
| 1 | Customer Support Resolution Agent | Agentic architecture, Tool design and MCP, Context management | `scenarios/customer_support_resolution/` (in progress) |
| 2 | Code Generation with Claude Code | Claude Code configuration and workflows, Context management | `scenarios/code_generation_with_claude_code/` (completed; expense tracker practice app) |
| 3 | Multi-Agent Research System | Agentic architecture, Tool design and MCP, Context management | not started |
| 4 | Developer Productivity with Claude | Tool design and MCP, Claude Code configuration, Agentic architecture | not started |
| 5 | Claude Code for Continuous Integration | Claude Code configuration, Prompt engineering and structured output | not started |
| 6 | Structured Data Extraction | Prompt engineering and structured output, Context management | not started |

## Development

```bash
ruff check .
mypy .
pytest        # inside a project that has tests, e.g. scenarios/code_generation_with_claude_code
```

Each scenario or project may have its own README and `pyproject.toml`; follow those when working inside it.
