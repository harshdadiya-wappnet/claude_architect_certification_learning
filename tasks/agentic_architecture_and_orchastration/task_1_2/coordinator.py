"""
Coordinator agent (hub). It is the only agent that talks to the user and the
only one that talks to subagents: all information flows through it.
"""
import asyncio

from tasks.agentic_architecture_and_orchastration.task_1_2.subagent import (
    MODEL,
    SUBAGENTS,
    client,
    extract_text,
    run_subagent,
)

MAX_ITERATIONS = 15  # runaway guard only; stop_reason is the real exit
MAX_TOKENS = 4096

COORDINATOR_PROMPT = """
You are a coordinator. You answer the user's request by delegating to specialist
subagents with the delegate_to_subagent tool, then returning one final answer.

Goal: a complete, correct, well-sourced answer. Quality criteria:
- Coverage: every part of the request is addressed.
- No duplication: give each subagent a distinct piece of work.
- Attribution: every claim in the final answer keeps its source (file path or calculation).
- Proportionality: simple requests need only the minimum number of subagents.
  Do not run every subagent when it is not needed.

How subagents work:
- They start with NO memory of this conversation. Everything they need must be in the
  `task` and `context` you send. Agents without file tools cannot see files: pass them the
  numbers they need. The synthesis_agent has no tools, so paste ALL relevant findings
  (as JSON, with their sources) into its `context`.
- Independent delegations can run in parallel: emit several delegate_to_subagent calls in
  the same response.
- If a subagent returns an error, decide whether to retry with a clearer task, use another
  agent, or continue with partial results and say clearly what is missing.

Before finishing, check your answer for gaps against the request. If something is missing,
delegate targeted follow-up work. Finish only when coverage is sufficient.

Available subagents:
{agents}
"""

DELEGATE_TOOL = {
    "name": "delegate_to_subagent",
    "description": "Delegate a task to a specialist subagent and get its result. Subagents have isolated context.",
    "input_schema": {
        "type": "object",
        "properties": {
            "agent": {"type": "string", "enum": list(SUBAGENTS), "description": "Which subagent to use."},
            "task": {"type": "string", "description": "What the subagent should do, as specific as possible."},
            "context": {
                "type": "string",
                "description": "Everything the subagent needs from earlier work (numbers, findings JSON). Empty if none.",
            },
        },
        "required": ["agent", "task"],
    },
}


def build_coordinator_prompt() -> str:
    agents = "\n".join(f"- {a.name}: {a.description}" for a in SUBAGENTS.values())
    return COORDINATOR_PROMPT.format(agents=agents)


async def delegate(block) -> dict:
    """Run one delegation; failures become is_error results the coordinator can react to."""
    args = block.input
    name = args.get("agent", "")
    task = args.get("task", "")
    print(f"\n[Delegate] {name}: {task[:100]}")
    try:
        if name not in SUBAGENTS:
            raise ValueError(f"Unknown subagent '{name}'. Available: {list(SUBAGENTS)}")
        result = await run_subagent(SUBAGENTS[name], task, args.get("context", ""))
        print(f"[Done]     {name} (tools: {result.tools_used or 'none'})")
        return {"type": "tool_result", "tool_use_id": block.id, "content": result.text}
    except Exception as e:
        print(f"[Failed]   {name}: {e}")
        return {"type": "tool_result", "tool_use_id": block.id,
                "content": f"Error: {e}", "is_error": True}


async def run_coordinator(request: str) -> str:
    """Run the coordinator loop for one request and return its final answer."""
    system = build_coordinator_prompt()  # static for the whole run
    messages = [{"role": "user", "content": request}]
    iterations = 0

    while True:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
            tools=[DELEGATE_TOOL],
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return extract_text(response.content)

        if response.stop_reason != "tool_use":
            return f"[Coordinator stopped with stop_reason={response.stop_reason}]"

        iterations += 1
        if iterations >= MAX_ITERATIONS:
            return "[Coordinator stopped: safety limit reached]"

        # Parallel subagents: all delegations from ONE response run concurrently,
        # and their results go back together in ONE user message.
        blocks = [b for b in response.content if b.type == "tool_use"]
        results = await asyncio.gather(*(delegate(b) for b in blocks))
        messages.append({"role": "user", "content": list(results)})
