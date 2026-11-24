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
| `tasks/` | Exam-guide task practice, one folder per task statement (see below) |
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
| 5 | Claude Code for Continuous Integration | Claude Code configuration, Prompt engineering and structured output | skipped (not planned) |
| 6 | Structured Data Extraction | Prompt engineering and structured output, Context management | `scenarios/structured_data_json/` (implemented; CLI, see below) |

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

### Structured Data Extraction (scenario 6)

A CLI agent that turns invoice text into JSON matching a Pydantic schema, using the Claude Agent SDK.

Run from the **repo root**:

```bash
python -m scenarios.structured_data_json.main
# then paste invoice text on one line, or:  /file scenarios/structured_data_json/samples/invoice_1.txt
```

- **Auth:** `CLAUDE_CODE_OAUTH_TOKEN` from `.env`, same as scenario 1.
- **Structured output:** `output_format` is set to the `Invoice` JSON schema (`schemas.py`); the validated result is read from `ResultMessage.structured_output` and re-checked with Pydantic.
- **Validation tool:** the agent calls an MCP tool, `validate_extraction` (`tools.py`), that checks the schema and the arithmetic (line items, subtotal, tax, total, date and currency formats), and fixes errors before answering.
- **No guessing:** fields the document does not state are `null`, with the reason in `notes`.
- **Tools:** built-in tools are off (`tools=[]`); only the validator is allowed, so documents come in through `/file`.
- **Samples:** `samples/` has a clean invoice and one with inconsistent totals.

## Exam guide tasks

Small focused exercises for individual task statements in the exam guide, under `tasks/`.

| Task | Folder | Status |
|---|---|---|
| 1.1 Agentic loops for autonomous task execution | `tasks/agentic_architecture_and_orchastration/task_1_1/` | implemented |
| 1.2 Coordinator-subagent multi-agent systems | `tasks/agentic_architecture_and_orchastration/task_1_2/` | implemented |

### Task 1.1: Agentic loop with math tools

A chat CLI where Claude decides when to call math tools (`calculate`, `solve_equation`, `solve_quadratic`, built on `sympy`) and the loop feeds results back until it is done.

Run from the **repo root**:

```bash
python -m tasks.agentic_architecture_and_orchastration.task_1_1.agentic_loops
# try: solve x**2+2*x-6=0
```

- **Loop control:** `stop_reason` drives the loop. `"tool_use"` runs the tools and calls the model again, `"end_turn"` stops. `max_tokens`, `refusal` and other reasons are reported explicitly. `MAX_TOOL_ITERATIONS` is only a runaway safety guard, and if it trips, pending tool calls are answered with an error result so the history stays valid.
- **History:** full assistant content blocks (including `tool_use`) are stored, and all `tool_result` blocks for a turn go back in one user message.
- **Model-driven:** no fixed tool sequence; the code only executes what Claude asks for. Tool errors are returned as `is_error` results so the model can recover.
- **Static system prompt:** thinking blocks are signed against the system prompt, so a prompt that changes between requests (for example a live timestamp) causes a 400 error. The date and time are instead added to each user message as a `[Context: ...]` tag.
- **Files:** `agentic_loops.py` (loop and CLI), `tools.py` (tool functions, schemas, registry, executor).

### Task 1.2: Coordinator with subagents

A coordinator agent delegates to specialist subagents on the raw Messages API (no Agent SDK), reusing the shared tools in `task_1_2/tools.py` (calculator tools and `read_file`).

```
user -> coordinator -> math_agent       (calculate, solve_equation, solve_quadratic)
                    -> file_agent       (read_file)
                    -> synthesis_agent  (no tools)
```

Run from the **repo root** (imports are absolute, so use `-m`):

```bash
python -m tasks.agentic_architecture_and_orchastration.task_1_2.main
# full pipeline: read the two files in task_1_2/samples/, compute total revenue and the break-even prices, then summarise
# minimal:       What is 15% of 2480?
```

- **Hub-and-spoke:** subagents never talk to each other; the coordinator relays everything and handles errors (a failed subagent comes back as an `is_error` result and the coordinator decides whether to retry, reroute or report partial results).
- **Isolated context:** every subagent call starts with a fresh `messages` list. Anything a subagent needs, such as numbers from a file, must be passed in `task` or `context`.
- **Delegation as a tool:** the coordinator has one `delegate_to_subagent` tool and decides which agents to use, so a simple question can skip the full pipeline.
- **Parallel subagents:** several delegations in one coordinator response run concurrently with `asyncio.gather`, and their results return together in one user message.
- **Tool restriction:** each subagent only sees its own subset of `tools.py`, and the runner rejects any other tool call.
- **Structured handoff:** `math_agent` and `file_agent` reply with JSON validated by pydantic (`Finding` = claim plus source), so attribution survives to the final answer.
- **Loop control:** `stop_reason` ends every loop, and the iteration caps are only runaway guards. System prompts are static (see 1.1).
- **Files:** `coordinator.py` (hub loop and delegate tool), `subagent.py` (runner, subagent definitions, report models), `tools.py`, `main.py` (CLI), `samples/` (test files).

## Development

```bash
ruff check .
mypy .
pytest        # inside a project that has tests, e.g. scenarios/code_generation_with_claude_code
```

Each scenario or project may have its own README and `pyproject.toml`; follow those when working inside it.
