import os
from pathlib import Path

from agents.document_analyse_agent import document_analysis_agent
from agents.genrate_report_agent import report_agent
from agents.synthisise_finding_agent import synthesis_agent
from agents.web_search_agent import web_research_agent
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

BASE_DIR = Path(__file__).resolve().parent.parent  # scenarios/multi_agent_architecture
REPORTS_DIR = BASE_DIR / "reports"

COORDINATOR_PROMPT = """
You are a research coordinator. You never research or write yourself; you delegate.
Only use the named subagents below (web_researcher, document_analyst, synthesiser, report_writer),
never `general-purpose`. If a subagent fails, report the error instead of working around it.

Workflow:
1. Delegate to `web_researcher` for web facts on the topic.
2. If a documents folder is given, delegate to `document_analyst` for it. Run steps 1 and 2 in parallel.
3. Pass BOTH sets of findings to `synthesiser`.
4. Pass the synthesis to `report_writer` to save the final report.
5. Reply with a short summary and the saved report path.

Skip step 2 if no documents folder is given. Always pass full findings between agents,
since they do not share context.
"""


def _resolve(raw: str) -> Path | None:
    """Resolve a tool path the way the tool will (expanding ~); None = unusable, so deny."""
    if not raw:
        return None
    p = Path(os.path.expanduser(raw))
    if not p.is_absolute():
        p = REPORTS_DIR / p
    return p.resolve()


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


async def guard_writes(input_data, tool_use_id, context):
    """PreToolUse hook: deny any file write whose resolved path is outside REPORTS_DIR."""
    tool_input = input_data.get("tool_input", {})
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    target = _resolve(raw)
    if target is not None and target.is_relative_to(REPORTS_DIR.resolve()):
        return {}
    return _deny(f"Writes are only allowed inside {REPORTS_DIR}")


def make_guard_reads(docs_dir: str | None):
    """PreToolUse hook factory: Read/Grep/Glob only inside REPORTS_DIR or the chosen docs folder."""
    allowed = [REPORTS_DIR.resolve()] + ([Path(docs_dir).resolve()] if docs_dir else [])

    def _ok(raw: str) -> bool:
        p = _resolve(raw)
        return p is not None and any(p.is_relative_to(a) for a in allowed)

    async def guard_reads(input_data, tool_use_id, context):
        ti = input_data.get("tool_input", {})
        # Read -> file_path; Grep/Glob -> path (missing means cwd = REPORTS_DIR).
        candidates = [ti.get("file_path") or ti.get("path") or str(REPORTS_DIR)]
        if input_data.get("tool_name") == "Glob":
            pattern = ti.get("pattern", "")
            # Glob patterns can carry their own base path: check absolute / ~ ones,
            # and reject any pattern that climbs out with ".." segments.
            if ".." in Path(pattern).parts:
                return _deny("Glob patterns may not contain '..'")
            if pattern.startswith(("/", "~")):
                candidates.append(pattern)
        if all(_ok(c) for c in candidates):
            return {}
        return _deny("Reads are only allowed in the reports folder or the chosen documents folder")

    return guard_reads


def build_options(docs_dir: str | None = None) -> ClaudeAgentOptions:
    REPORTS_DIR.mkdir(exist_ok=True)

    # Same auth as customer_support_resolution/main.py: OAuth token from .env.
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not oauth_token:
        raise RuntimeError("CLAUDE_CODE_OAUTH_TOKEN is not set (add it to .env)")
    # An API key in the environment takes precedence over the OAuth token,
    # so remove it to make sure OAuth is the only auth source.
    os.environ.pop("ANTHROPIC_API_KEY", None)

    return ClaudeAgentOptions(
        env={"CLAUDE_CODE_OAUTH_TOKEN": oauth_token},
        setting_sources=[],  # ignore user/project Claude Code settings
        include_partial_messages=True,  # emit StreamEvent messages for token streaming
        # Reading a PDF returns it base64-encoded in one JSON message; the 1 MB default is too small.
        max_buffer_size=32 * 1024 * 1024,
        system_prompt=COORDINATOR_PROMPT,
        model="claude-sonnet-5-5",
        agents={
            "web_researcher": web_research_agent,
            "document_analyst": document_analysis_agent,
            "synthesiser": synthesis_agent,
            "report_writer": report_agent,
        },
        # Subagents can only use tools their parent has, so the session tool set must be the
        # union of everything the subagents need. Bash/Edit/etc. are deliberately left out.
        # Each subagent's own `tools=` list still limits what it can use, and the coordinator
        # is told in its prompt to delegate rather than work itself.
        tools=["Agent", "Task", "WebSearch", "WebFetch", "Read", "Grep", "Glob", "Write"],
        # Pre-approve what the subagents use so the headless run never waits for a prompt;
        # Write is still confined to REPORTS_DIR by the hook below.
        allowed_tools=["Agent", "Task", "WebSearch", "WebFetch", "Read", "Grep", "Glob", "Write"],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="Write|Edit|MultiEdit|NotebookEdit", hooks=[guard_writes]),
                HookMatcher(matcher="Read|Grep|Glob", hooks=[make_guard_reads(docs_dir)]),
            ]
        },
        cwd=str(REPORTS_DIR),  # not the project root, so .env and source stay out of reach
        add_dirs=[docs_dir] if docs_dir else [],
        max_turns=30,
    )
