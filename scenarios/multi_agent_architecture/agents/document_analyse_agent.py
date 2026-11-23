from claude_agent_sdk import AgentDefinition

document_analysis_agent = AgentDefinition(
    description="Analyzes documents and extracts relevant information.",
    prompt="""
    Analyze the provided documents.
    Extract important facts and include source references.
    Clearly identify missing information.
    """,
    model="claude-haiku-5-5",
    tools=["Read", "Grep", "Glob"],
    maxTurns=10
)