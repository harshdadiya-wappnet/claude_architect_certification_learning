"""Developer productivity assistant (Streamlit).

Run from the repo root:  streamlit run scenarios/developer_productivity_claude/main.py
"""
import asyncio
import os
import re
import shlex
import sys
from pathlib import Path

# agent.py imports via `scenarios.…`, so the repo root must be importable.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import streamlit as st
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    StreamEvent,
    ToolUseBlock,
    query,
)
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

WORKSPACE = Path(__file__).resolve().parent / "workspace"

ORCHESTRATOR_PROMPT = """
You are a thin router. Delegate every user request to the `developer_productivity`
subagent and relay its answer. Do not do the work yourself.
"""

# Read-only GitHub MCP tools (verify names against the server's tool list).
GITHUB_READ_TOOLS = [
    "mcp__remote__get_file_contents",
    "mcp__remote__search_code",
    "mcp__remote__search_repositories",
    "mcp__remote__list_commits",
    "mcp__remote__list_issues",
    "mcp__remote__get_issue",
    "mcp__remote__list_pull_requests",
    "mcp__remote__get_pull_request",
]
GITHUB_WRITE_TOOLS = [
    "mcp__remote__create_or_update_file",
    "mcp__remote__delete_file",
    "mcp__remote__push_files",
    "mcp__remote__merge_pull_request",
    "mcp__remote__create_pull_request",
    "mcp__remote__create_issue",
    "mcp__remote__add_issue_comment",
    "mcp__remote__create_branch",
    "mcp__remote__fork_repository",
    "mcp__remote__create_repository",
]

# Bash is limited to a few read-only git commands, checked argument by argument.
SHELL_META = set(";&|`$<>(){}\\\n\r*?!#")
ALLOWED_GIT_FLAGS = {
    "status": None,  # None = any flag not in the denylist
    "log": None,
    "diff": None,
    "show": None,
    "branch": {"-a", "-r", "-v", "-vv", "--list", "--show-current"},
    "remote": {"-v"},
}
DENIED_FLAG_PREFIXES = (
    "--output", "--ext-diff", "--textconv", "--exec", "--open-files-in-pager",
    "--git-dir", "--work-tree", "--no-index", "-c", "-C", "-O",
)
# `git clone` is the one write-ish command allowed: GitHub https URL, no flags,
# plain folder name, and only when the working directory is inside WORKSPACE.
CLONE_URL = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+?(\.git)?/?")
CLONE_DEST = re.compile(r"[\w][\w.-]*")


def clone_error(argv: list[str], cwd: str | None) -> str | None:
    if not cwd or not Path(cwd).resolve().is_relative_to(WORKSPACE.resolve()):
        return f"git clone is only allowed inside {WORKSPACE}"
    args = argv[2:]
    if not 1 <= len(args) <= 2:
        return "usage: git clone <https://github.com/owner/repo> [folder]"
    if not CLONE_URL.fullmatch(args[0]):
        return "git clone only accepts https://github.com/<owner>/<repo> URLs, no flags"
    if len(args) == 2 and not CLONE_DEST.fullmatch(args[1]):
        return "clone folder must be a plain name (no paths, no leading dash)"
    return None


def git_command_error(command: str, cwd: str | None = None) -> str | None:
    """Return a reason to deny `command`, or None if it is an allowed git call."""
    if any(ch in SHELL_META for ch in command):
        return "shell metacharacters are not allowed"
    try:
        argv = shlex.split(command)
    except ValueError:
        return "unparseable command"
    if len(argv) >= 2 and argv[0] == "git" and argv[1] == "clone":
        return clone_error(argv, cwd)
    if len(argv) < 2 or argv[0] != "git" or argv[1] not in ALLOWED_GIT_FLAGS:
        return f"only read-only git commands (and clone in workspace/) are allowed: {', '.join(ALLOWED_GIT_FLAGS)}"
    allowed = ALLOWED_GIT_FLAGS[argv[1]]
    for arg in argv[2:]:
        if arg.startswith("-"):
            if arg.startswith(DENIED_FLAG_PREFIXES):
                return f"flag not allowed: {arg}"
            if allowed is not None and arg not in allowed:
                return f"flag not allowed for git {argv[1]}: {arg}"
        elif allowed is not None:
            return f"arguments not allowed for git {argv[1]}: {arg}"
    return None


async def bash_guard(input_data, tool_use_id, context):
    """PreToolUse hook: deny any Bash call that is not an allowed git command."""
    reason = git_command_error(
        input_data.get("tool_input", {}).get("command", ""), input_data.get("cwd")
    )
    if reason is None:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


st.set_page_config(page_title="Dev Productivity", page_icon="🛠️")
st.title("🛠️ Developer Productivity Agent")

try:
    from scenarios.developer_productivity_claude.agent import (
        build_system_prompt,
        developer_productivity_agent,
    )
except RuntimeError as e:  # e.g. GITHUB_TOKEN missing
    st.error(str(e))
    st.stop()


def build_options(cwd: Path, session_id: str | None) -> ClaudeAgentOptions:
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not oauth_token:
        raise RuntimeError("CLAUDE_CODE_OAUTH_TOKEN is not set (add it to .env)")
    os.environ.pop("ANTHROPIC_API_KEY", None)  # make OAuth the only auth source

    developer_productivity_agent.prompt = build_system_prompt()  # fresh date/time
    return ClaudeAgentOptions(
        env={"CLAUDE_CODE_OAUTH_TOKEN": oauth_token},
        setting_sources=[],
        include_partial_messages=True,
        system_prompt=ORCHESTRATOR_PROMPT,
        model="claude-sonnet-5-5",
        cwd=cwd,
        resume=session_id,
        agents={"developer_productivity": developer_productivity_agent},
        # Session tool set must cover what the subagent needs (it inherits these).
        tools=["Agent", "Task", "Bash", "Read", "Grep", "Glob"],
        # Bash is allowed only through bash_guard (read-only git); the hook can deny
        # but never widens access. GitHub MCP is limited to explicit read-only tools.
        allowed_tools=["Read", "Grep", "Glob", "Agent", "Task", "Bash", *GITHUB_READ_TOOLS],
        disallowed_tools=GITHUB_WRITE_TOOLS,
        hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[bash_guard])]},
    )


def describe_tool(block: ToolUseBlock, who: str) -> str:
    """One readable line per tool call, including the interesting argument."""
    args = block.input or {}
    detail = (
        args.get("command")
        or args.get("file_path")
        or args.get("path")
        or args.get("pattern")
        or args.get("query")
        or args.get("description")
        or ""
    )
    name = block.name.removeprefix("mcp__remote__")
    suffix = f": `{str(detail)[:120]}`" if detail else ""
    return f"🔧 **{name}** ({who}){suffix}"


def render_tools(container, tools: list[str]) -> None:
    for line in tools:
        container.markdown(line)


async def run_turn(prompt: str, cwd: Path, session_id: str | None, tool_box, answer):
    """Stream one turn. Tool calls go to `tool_box` (collapsible), text to `answer`."""
    result, text, tools = None, "", []
    async for msg in query(prompt=prompt, options=build_options(cwd, session_id)):
        if isinstance(msg, StreamEvent):
            ev = msg.event
            if (
                msg.parent_tool_use_id is None
                and ev.get("type") == "content_block_delta"
                and ev.get("delta", {}).get("type") == "text_delta"
            ):
                text += ev["delta"]["text"]
                answer.markdown(text)
        elif isinstance(msg, AssistantMessage):
            who = "subagent" if msg.parent_tool_use_id else "router"
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    line = describe_tool(block, who)
                    tools.append(line)
                    tool_box.markdown(line)
        elif isinstance(msg, ResultMessage):
            result = msg
    return result, text, tools


with st.sidebar:
    st.header("Repository")
    repo = st.text_input("Working directory", value=str(WORKSPACE))
    st.caption("Clone other repos into `workspace/` to test git operations safely.")
    subdirs = sorted(p.name for p in WORKSPACE.iterdir() if (p / ".git").exists()) if WORKSPACE.exists() else []
    if subdirs:
        picked = st.selectbox("Or pick a cloned repo", ["—", *subdirs])
        if picked != "—":
            repo = str(WORKSPACE / picked)
    if st.button("New conversation"):
        st.session_state.clear()
        st.rerun()

cwd = Path(repo).expanduser()
if not cwd.is_dir():
    st.error(f"Directory not found: {cwd}")
    st.stop()
st.caption(f"📁 {cwd}")

st.session_state.setdefault("history", [])
st.session_state.setdefault("session_id", None)
# Sessions started before the dict format stored (role, content) tuples; convert them.
st.session_state.history = [
    {"role": m[0], "content": m[1]} if isinstance(m, tuple) else m
    for m in st.session_state.history
]


def show_message(msg: dict) -> None:
    """Render a stored message: answer first, tool calls in a collapsed toggle."""
    with st.chat_message(msg["role"]):
        if msg.get("tools"):
            with st.expander(f"🔧 Tool calls ({len(msg['tools'])})", expanded=False):
                render_tools(st, msg["tools"])
        st.markdown(msg["content"])
        if msg.get("stats"):
            st.caption(msg["stats"])


for msg in st.session_state.history:
    show_message(msg)

if prompt := st.chat_input("Ask about the code, or run a git task…"):
    st.chat_message("user").markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        # Two fixed containers, in order: tool toggle on top, answer below. Writing via
        # object methods (not `with` blocks) keeps each element in its own container.
        tool_slot = st.container()
        answer_slot = st.container()
        status = tool_slot.status("Working…", expanded=False)
        answer = answer_slot.empty()
        result, text, tools = asyncio.run(
            run_turn(prompt, cwd, st.session_state.session_id, status, answer)
        )
        failed = not result or result.is_error
        status.update(
            label=f"🔧 Tool calls ({len(tools)})" if tools else "Done",
            state="error" if failed else "complete",
        )
        final = (result.result if result and result.result else text) or "_No response._"
        answer.markdown(final)
        stats = ""
        if result:
            cost = f"${result.total_cost_usd:.4f}" if result.total_cost_usd is not None else "n/a"
            stats = f"{result.num_turns} turns · {result.duration_ms / 1000:.1f}s · cost {cost}"
            answer_slot.caption(stats)
    st.session_state.history.append(
        {"role": "assistant", "content": final, "tools": tools, "stats": stats}
    )
    if result:
        st.session_state.session_id = result.session_id
