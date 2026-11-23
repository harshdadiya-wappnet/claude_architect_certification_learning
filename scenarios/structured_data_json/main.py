"""Structured data extraction CLI.

Run from the repo root:  python -m scenarios.structured_data_json.main
Commands: paste invoice text on one line, or  /file <path>  to load a document. exit/quit stops.
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import AssistantMessage, ResultMessage, ToolUseBlock
from dotenv import load_dotenv
from pydantic import ValidationError

from scenarios.structured_data_json.prompts import SYSTEM_PROMPT
from scenarios.structured_data_json.schemas import OUTPUT_FORMAT, Invoice
from scenarios.structured_data_json.tools import extraction_mcp_server

load_dotenv()

SYSTEM_PROMPT = SYSTEM_PROMPT.format(current_date=datetime.now().strftime("%Y-%m-%d"))

oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
if not oauth_token:
    raise RuntimeError("CLAUDE_CODE_OAUTH_TOKEN is not set (add it to .env)")

# An API key in the environment takes precedence over the OAuth token,
# so remove it to make sure OAuth is the only auth source.
os.environ.pop("ANTHROPIC_API_KEY", None)

claude_agent_options = ClaudeAgentOptions(
    model="claude-haiku-5-5",
    system_prompt=SYSTEM_PROMPT,
    env={"CLAUDE_CODE_OAUTH_TOKEN": oauth_token},
    mcp_servers={"extraction": extraction_mcp_server},
    # Only the validator may run; no file/shell tools, so documents come in via /file.
    tools=[],
    allowed_tools=["mcp__extraction__validate_extraction"],
    # The final answer must match the Invoice schema -> ResultMessage.structured_output.
    output_format=OUTPUT_FORMAT,
    setting_sources=[],
)


def load_input(user_query: str) -> str | None:
    """Return the document text for a /file command, the raw text otherwise."""
    if not user_query.startswith("/file "):
        return user_query
    path = Path(user_query.removeprefix("/file ").strip()).expanduser()
    if not path.is_file():
        print(f"File not found: {path}")
        return None
    return path.read_text()


async def extract(client: ClaudeSDKClient, document: str) -> None:
    await client.query(f"Extract this invoice:\n\n{document}")

    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[calling {block.name.removeprefix('mcp__extraction__')}...]", flush=True)
        elif isinstance(message, ResultMessage):
            if message.is_error or message.structured_output is None:
                print(f"Extraction failed (stop_reason={message.stop_reason}).")
                return
            try:
                invoice = Invoice.model_validate(message.structured_output)
            except ValidationError as e:
                print(f"Output did not match the schema:\n{e}")
                return
            print(invoice.model_dump_json(indent=2))
            cost = message.total_cost_usd
            print(f"[{message.num_turns} turns, cost ${cost:.4f}]" if cost is not None else "")


async def main():
    # Each document is independent, but one client keeps the process/startup cost to once.
    async with ClaudeSDKClient(options=claude_agent_options) as client:
        while True:
            user_query = input("Paste invoice text or /file <path> (exit to quit): ").strip()
            if user_query.lower() in ["exit", "quit"]:
                print("Exiting...")
                break
            if not user_query:
                continue
            document = load_input(user_query)
            if document is not None:
                await extract(client, document)


if __name__ == "__main__":
    asyncio.run(main())
