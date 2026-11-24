"""
To use this agentic loop we can use below command:
python -m tasks.agentic_architecture_and_orchastration.task_1_1.agentic_loops
"""
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from tasks.agentic_architecture_and_orchastration.task_1_1.tools import tools, tool_execute


load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

tz = ZoneInfo("Asia/Kolkata")

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 1024
MAX_TOOL_ITERATIONS = 10  # safety cap so the loop can never run forever

SYSTEM_PROMPT = """
You are an helpful AI assistant named Harsh.
Your job is to help user in day to day tasks and engage in small conversations.

Guidelines for chat:
1. Your answers should be to the point and concise.
2. You should help user and teach new topics and areas but dont just solve or do tasks, just guide them.
3. Don't engage in harmful and abusive activity.
4. For any math (arithmetic, equations, quadratics) use the provided tools instead of calculating yourself.

The current date and time are given at the start of each user message in a [Context: ...] tag.
"""


def with_context(user_query: str) -> str:
    """
    Prefix the user message with the current date/time.

    The system prompt must stay static: thinking blocks are signed against it,
    so changing it between requests causes a 400 error. A user message is saved
    once in history and never changes, so it is safe to carry dynamic context.
    """
    now = datetime.now(tz=tz)
    return (
        f"[Context: date={now.strftime('%Y-%m-%d')} (YYYY-MM-DD), "
        f"time={now.strftime('%I:%M:%S %p')}]\n{user_query}"
    )


async def append_user_message(messages: list[MessageParam], user_input_message) -> list[MessageParam]:
    """
    Append the user message (plain text or a list of tool_result blocks)
    to the messages list to keep the conversation history.
    """
    messages.append({
        "role": "user",
        "content": user_input_message
    })
    return messages


async def append_assistant_message(messages: list[MessageParam], assistant_output) -> list[MessageParam]:
    """
    Append the assistant output (text or full content blocks incl. tool_use)
    to the messages list to keep the full conversation.
    """
    messages.append({
        "role": "assistant",
        "content": assistant_output
    })
    return messages


async def run_tools(content_blocks) -> list[dict]:
    """
    Execute every tool_use block in an assistant turn and build the
    matching tool_result blocks (all returned together in one user message).
    """
    tool_results = []

    for block in content_blocks:
        if block.type != "tool_use":
            continue

        try:
            result = await tool_execute(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result),
            })
        except Exception as e:
            # Let the model see the failure and recover instead of crashing
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"Error: {e}",
                "is_error": True,
            })

    return tool_results


async def chat(messages: list[MessageParam], user_query: str) -> None:
    """
    Agentic loop. The model's stop_reason drives control flow:
      - "tool_use"  -> run the requested tools, append results, call again
      - "end_turn"  -> the model is finished, stop
      - anything else (max_tokens, refusal, ...) -> report it and stop
    MAX_TOOL_ITERATIONS is only a runaway-loop safety guard, not the
    normal way the loop ends.
    """
    await append_user_message(messages, with_context(user_query))

    iterations = 0

    while True:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        ) as stream:
            async for chunk in stream.text_stream:
                print(chunk, end="", flush=True)
            response = await stream.get_final_message()

        # Store full content blocks (text + tool_use), not just the text
        await append_assistant_message(messages, response.content)

        if response.stop_reason == "end_turn":
            return

        if response.stop_reason == "tool_use":
            iterations += 1
            if iterations >= MAX_TOOL_ITERATIONS:
                # Safety net only: never reached in a healthy conversation.
                # Note history ends on an assistant tool_use turn here, so
                # answer it to keep the conversation valid for the next turn.
                await append_user_message(messages, [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Tool call skipped: iteration limit reached.",
                        "is_error": True,
                    }
                    for block in response.content
                    if block.type == "tool_use"
                ])
                print("\n[Stopped: safety limit on tool iterations reached]")
                return

            tool_results = await run_tools(response.content)
            await append_user_message(messages, tool_results)
            continue

        # Explicitly handle the non-normal endings instead of treating
        # them like a clean finish.
        if response.stop_reason == "max_tokens":
            print("\n[Response cut off: max_tokens reached]")
        elif response.stop_reason == "refusal":
            print("\n[The model declined to respond]")
        else:
            print(f"\n[Stopped with unexpected stop_reason: {response.stop_reason}]")
        return


async def main():
    messages: list[MessageParam] = []

    print("Claude Chat with Math Tools")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = await asyncio.to_thread(input, "You: ")

        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not user_input.strip():
            continue

        print("Assistant: ", end="", flush=True)

        history_len = len(messages)
        try:
            await chat(messages, user_input)
        except Exception as e:
            print(f"\nError: {e}")
            # Roll back the failed turn so history stays valid
            del messages[history_len:]

        print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nChat interrupted.")
