"""Multi-agent research app.

Run from this folder:  streamlit run main.py
"""
import asyncio
from pathlib import Path

import streamlit as st
from agents.coordinaet_agent import REPORTS_DIR, build_options
from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    StreamEvent,
    ToolUseBlock,
    query,
)
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

st.set_page_config(page_title="Multi-Agent Research", page_icon="🧠")
st.title("🧠 Multi-Agent Research")
st.caption("Coordinator → web researcher + document analyst → synthesiser → report writer")

topic = st.text_area("Research topic", placeholder="e.g. Current state of small modular reactors")
docs_dir = st.text_input("Documents folder (optional)", placeholder="/path/to/docs")
run = st.button("Run research", type="primary", disabled=not topic.strip())


async def run_pipeline(prompt: str, docs: str | None, log, answer, sub_box) -> ResultMessage | None:
    """Stream the coordinator run token-by-token, logging delegations and tool calls."""
    result = None
    coordinator_text = ""  # coordinator tokens, shown in `answer`
    sub_text = ""  # current subagent's tokens, shown (tail only) in `sub_box`

    async for msg in query(prompt=prompt, options=build_options(docs)):
        if isinstance(msg, StreamEvent):
            event = msg.event
            is_sub = msg.parent_tool_use_id is not None
            etype = event.get("type")
            if etype == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    if is_sub:
                        sub_text += delta["text"]
                        sub_box.caption("🧩 subagent output (live): …" + sub_text[-400:])
                    else:
                        coordinator_text += delta["text"]
                        answer.markdown(coordinator_text)
            elif etype == "content_block_stop":
                if is_sub:
                    sub_text = ""
                elif coordinator_text and not coordinator_text.endswith("\n\n"):
                    coordinator_text += "\n\n"

        elif isinstance(msg, AssistantMessage):
            # Text was already streamed via deltas; only surface tool calls here.
            who = "subagent" if msg.parent_tool_use_id else "coordinator"
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    if block.name in ("Agent", "Task"):
                        target = block.input.get("subagent_type", "?")
                        log.write(f"🤝 **delegating → `{target}`**: {block.input.get('description', '')}")
                    else:
                        log.write(f"🔧 `{who}` used `{block.name}`")
        elif isinstance(msg, ResultMessage):
            result = msg
    return result


if run:
    prompt = f"Research this topic and produce a report: {topic.strip()}"
    docs = docs_dir.strip() or None
    if docs:
        if not Path(docs).is_dir():
            st.error(f"Documents folder not found: {docs}")
            st.stop()
        prompt += f"\nDocuments folder to analyse: {docs}"

    with st.status("Agents working...", expanded=True) as status:
        answer = st.empty()
        sub_box = st.empty()
        result = asyncio.run(run_pipeline(prompt, docs, st, answer, sub_box))
        sub_box.empty()
        status.update(label="Done", state="complete" if result and not result.is_error else "error")

    if result:
        st.subheader("Result")
        st.markdown(result.result or "_No final text returned._")
        cost = f"${result.total_cost_usd:.4f}" if result.total_cost_usd is not None else "n/a"
        st.caption(f"{result.num_turns} turns · {result.duration_ms / 1000:.1f}s · cost {cost}")

    reports = sorted(REPORTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if reports:
        st.download_button("Download latest report", reports[0].read_text(), file_name=reports[0].name)
