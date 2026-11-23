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
| 3 | Multi-Agent Research System | Agentic architecture, Tool design and MCP, Context management | `scenarios/multi_agent_architecture/` (implemented; Streamlit app, see below) |
| 4 | Developer Productivity with Claude | Tool design and MCP, Claude Code configuration, Agentic architecture | `scenarios/developer_productivity_claude/` (implemented; Streamlit app, see below) |
| 5 | Claude Code for Continuous Integration | Claude Code configuration, Prompt engineering and structured output | not started |
| 6 | Structured Data Extraction | Prompt engineering and structured output, Context management | not started |

### Multi-Agent Research System (scenario 3)

A coordinator agent delegates to four specialist subagents built with the Claude Agent SDK:

```
coordinator -> web_researcher    (WebSearch, WebFetch)
            -> document_analyst  (Read, Grep, Glob)
            -> synthesiser       (no tools)
            -> report_writer     (Write, saves to reports/)
```

Run the Streamlit app from the scenario folder:

```bash
cd scenarios/multi_agent_architecture
../../.venv/bin/streamlit run main.py
```

- **Auth:** reads `CLAUDE_CODE_OAUTH_TOKEN` from `.env` (an `ANTHROPIC_API_KEY` in the environment is removed so OAuth is the only source), same as `scenarios/customer_support_resolution/`.
- **Streaming:** coordinator text streams token by token; delegations and tool calls appear in a live log.
- **Guardrails:** the session `cwd` is `reports/`; `PreToolUse` hooks deny writes outside `reports/` and reads outside `reports/` or the documents folder you enter in the UI. Point that folder at documents only, never at anything containing secrets.
- **Output:** reports are saved to `scenarios/multi_agent_architecture/reports/`.
- **Cost:** each run makes several model calls across the agents, so start with a narrow topic.

### Developer Productivity with Claude (scenario 4)

A router session delegates every request to a `developer_productivity` subagent (an `AgentDefinition`) that has the GitHub remote MCP server attached inline, plus local read-only git through Bash.

Run the Streamlit app from the **repo root** (the code imports through `scenarios.…`):

```bash
git clone <repo-url> scenarios/developer_productivity_claude/workspace/<name>   # optional: a repo to test on
streamlit run scenarios/developer_productivity_claude/main.py
```

- **Auth:** `CLAUDE_CODE_OAUTH_TOKEN` and `GITHUB_TOKEN` in `.env` (importing `external_tools.py` raises if `GITHUB_TOKEN` is missing). Use a fine-grained token limited to the repos you test with and read-only Metadata, Contents, Issues and Pull requests.
- **Workspace:** `scenarios/developer_productivity_claude/workspace/` is a sandbox for cloning other repos; everything in it except its README is git-ignored. The sidebar lists cloned repos and sets the agent's working directory.
- **Guardrails (`main.py`):** a `PreToolUse` hook (`bash_guard`) allows only `git status/log/diff/show/branch/remote` with a safe flag list, plus `git clone https://github.com/<owner>/<repo> [folder]` (no flags) when the working directory is inside `workspace/`. Shell metacharacters are rejected. GitHub MCP is limited to an explicit read-only tool list and write tools are in `disallowed_tools`. A cloned repo's own `.git/config` is not sandboxed, so clone only repos you trust.
- **UI:** the answer streams as plain text; tool calls are in a collapsible `🔧 Tool calls (N)` box above it. Conversation memory uses the SDK `resume` session id; **New conversation** resets it.
- **Files:** `agent.py` (agent definition and prompt), `external_tools.py` (GitHub MCP config), `main.py` (app, guardrails).

## Development

```bash
ruff check .
mypy .
pytest        # inside a project that has tests, e.g. scenarios/code_generation_with_claude_code
```

Each scenario or project may have its own README and `pyproject.toml`; follow those when working inside it.
