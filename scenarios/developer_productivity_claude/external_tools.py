import os

from claude_agent_sdk import McpServerConfig
from dotenv import load_dotenv

load_dotenv()

github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise RuntimeError("GITHUB_TOKEN is not set; add it to your .env file.")

mcp_server: dict[str, McpServerConfig] = {
    "remote": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {"Authorization": f"Bearer {github_token}"},
    }
}
