from claude_agent_sdk import AgentDefinition

synthesis_agent = AgentDefinition(
    description="Merges findings from the web researcher and document analyst into one consistent set of conclusions.",
    prompt="""
    You receive findings from other agents (web research and document analysis).
    - Merge them, remove duplicates, and group by theme.
    - Flag contradictions between sources and say which source is more reliable.
    - Keep every source reference (URL or file path) next to its claim.
    - Clearly list gaps: what could not be verified.
    Return structured markdown. Do not add facts that are not in the input.
    """,
    model="claude-sonnet-5-5",
    tools=[],  # pure reasoning, no tool access needed
    maxTurns=5,
)
