from claude_agent_sdk import AgentDefinition

web_research_agent = AgentDefinition(
    description="Searches the web and gathers reliable sources.",
    prompt="""
    Research the assigned topic.
    Gather relevant facts, source URLs, and publication dates.
    Do not invent citations.
    """,
    model="claude-haiku-5-5",
    tools=["WebSearch", "WebFetch"],
    maxTurns=10
)