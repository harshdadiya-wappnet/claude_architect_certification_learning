import asyncio
import os
from typing import List, Literal
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Initialize Async Anthropic client
client = AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

MODEL = "claude-haiku-5-5"


# ---------------------------------------------------------------------------
# 1. Define your Structured Output Schema using Pydantic
# ---------------------------------------------------------------------------
class Entity(BaseModel):
    name: str = Field(description="The name of the entity")
    category: Literal["person", "organization", "location", "product", "other"] = Field(
        description="The category of the entity"
    )


class TextAnalysis(BaseModel):
    summary: str = Field(description="A concise 1-2 sentence summary of the text")
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall sentiment of the input text"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    entities: List[Entity] = Field(
        default_factory=list, description="Key entities extracted from the text"
    )
    tags: List[str] = Field(
        default_factory=list, description="Relevant topic tags or keywords"
    )


# ---------------------------------------------------------------------------
# Method 1: Native client.messages.parse (Recommended for modern SDK)
# ---------------------------------------------------------------------------
async def extract_structured_data_native(prompt: str) -> TextAnalysis:
    """Uses Anthropic SDK's built-in `client.messages.parse` method with Pydantic."""
    print("--- Running Method 1: Native messages.parse ---")

    response = await client.messages.parse(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        output_format=TextAnalysis,  # Directly pass the Pydantic class
    )

    # The result is automatically parsed and validated into your Pydantic model
    parsed_data: TextAnalysis = response.parsed_output
    return parsed_data


# ---------------------------------------------------------------------------
# Method 2: Forced Tool Calling (Universal pattern across all Claude models)
# ---------------------------------------------------------------------------
async def extract_structured_data_tool_choice(prompt: str) -> TextAnalysis:
    """Uses forced tool choice (`tool_choice={'type': 'tool', ...}`) to guarantee structured JSON."""
    print("\n--- Running Method 2: Forced Tool Calling ---")

    tool_name = "record_text_analysis"

    response = await client.messages.create(
        model=MODEL,
        max_tokens=1000,
        tools=[
            {
                "name": tool_name,
                "description": "Record structured analysis of text",
                "input_schema": TextAnalysis.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": tool_name},  # Force Claude to use this tool
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the tool input from response content blocks
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return TextAnalysis.model_validate(block.input)

    raise RuntimeError("Model did not return expected tool call block.")


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------
async def main():
    sample_text = (
        "Acme Corp announced yesterday in San Francisco that their CEO, Jane Doe, "
        "will unveil a breakthrough quantum computing chip next month. "
        "Investors were thrilled, sending stock prices surging by 14%."
    )

    print(f"Input text:\n\"{sample_text}\"\n")

    # Method 1: Native
    result1 = await extract_structured_data_native(sample_text)
    print("Native parsed output:")
    print(result1.model_dump_json(indent=2))

    # Method 2: Tool choice
    result2 = await extract_structured_data_tool_choice(sample_text)
    print("\nTool choice parsed output:")
    print(result2.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
