from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, StreamEvent, ToolUseBlock
from claude_agent_sdk import McpSdkServerConfig
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime

from scenarios.customer_support_resolution.prompts import SYSTEM_PROMPT
from scenarios.customer_support_resolution.tools import customer_support_mcp_server
load_dotenv()

SYSTEM_PROMPT = SYSTEM_PROMPT.format(current_date=datetime.now().strftime("%Y-%m-%d"))

oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
if not oauth_token:
    raise RuntimeError("CLAUDE_CODE_OAUTH_TOKEN is not set (add it to .env)")

# An API key in the environment takes precedence over the OAuth token,
# so remove it to make sure OAuth is the only auth source.
os.environ.pop("ANTHROPIC_API_KEY", None)

claude_agent_options: ClaudeAgentOptions = ClaudeAgentOptions(
    model="claude-haiku-5-5",
    system_prompt=SYSTEM_PROMPT,
    env={"CLAUDE_CODE_OAUTH_TOKEN": oauth_token},
    mcp_servers={
        "customer_support": customer_support_mcp_server
    },
    permission_mode="acceptEdits",
    # Pre-approve these tools so they run without a permission prompt
    # (this script has no way to answer one).
    allowed_tools=[
        "mcp__customer_support__get_customer",
        "mcp__customer_support__lookup_order",
        "mcp__customer_support__process_refund",
        "mcp__customer_support__escalate_to_human_support"
    ],
    setting_sources=[],
    # Emit StreamEvent messages (raw API events) so we can print text as it arrives.
    include_partial_messages=True,
)

async def chat(client: ClaudeSDKClient, user_query: str):
    # Reuse the same client so the session keeps the conversation history.
    await client.query(user_query)

    streaming_text = False  # True while we're mid-way through printing a text block

    # The loop ends on its own after the final ResultMessage, across all tool-call turns.
    async for message in client.receive_response():
        if isinstance(message, StreamEvent):
            event = message.event
            event_type = event.get("type")

            if event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    if not streaming_text:
                        print("Assistant: ", end="", flush=True)
                        streaming_text = True
                    print(delta["text"], end="", flush=True)

            elif event_type == "content_block_stop" and streaming_text:
                print()  # finish the line when a text block ends
                streaming_text = False

        elif isinstance(message, AssistantMessage):
            # Text was already streamed via deltas; only surface tool calls here.
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[calling {block.name}...]", flush=True)


async def main():
    # One client for the whole conversation, not one per message.
    async with ClaudeSDKClient(options=claude_agent_options) as client:
        while True:
            user_query = input("Enter your query: ")
            if user_query.lower() in ["exit", "quit"]:
                print("Exiting...")
                break
            await chat(client, user_query)

if __name__ == "__main__":
    asyncio.run(main())
            
