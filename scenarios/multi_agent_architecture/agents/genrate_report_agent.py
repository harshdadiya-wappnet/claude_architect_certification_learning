from claude_agent_sdk import AgentDefinition

report_agent = AgentDefinition(
    description="Writes the final markdown report from synthesised findings and saves it to the reports/ folder.",
    prompt="""
    Write a clear, well-structured markdown report from the synthesised findings you are given:
    1. Title and one-paragraph executive summary
    2. Key findings (with source references)
    3. Contradictions / gaps
    4. Sources list
    Save it with the Write tool as <short-kebab-case-topic>.md in the current directory (the reports folder; writes elsewhere are blocked) and reply with the
    saved file path followed by the full report text. Do not invent facts or sources.
    """,
    model="claude-sonnet-5-5",
    tools=["Write"],
    maxTurns=5,
)
