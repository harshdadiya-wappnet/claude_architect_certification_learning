from datetime import datetime
from zoneinfo import ZoneInfo

from claude_agent_sdk import AgentDefinition

from scenarios.developer_productivity_claude.external_tools import mcp_server

time_zone = ZoneInfo("Asia/Kolkata")

SYSTEM_PROMPT_TEMPLATE = """
You are a developer assistant that helps users understand code, understand systems \
and write repetitive boilerplate code.

Use appropriate tools for user requests which do tasks.

Responses should be brief and to the point.

Use current date and time information if needed, with date in YYYY-MM-DD format \
and time in 12 hrs format with AM and PM.
Current Date: {date}
Current Time: {time}
"""


def build_system_prompt() -> str:
    """Build the system prompt with the current date and time (call per session)."""
    now = datetime.now(tz=time_zone)
    return SYSTEM_PROMPT_TEMPLATE.format(
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%I:%M:%S %p"),
    )


developer_productivity_agent = AgentDefinition(
    description="This agent enhances the productivity of developers and helps them in their work.",
    prompt=build_system_prompt(),
    mcpServers=[mcp_server],
)
