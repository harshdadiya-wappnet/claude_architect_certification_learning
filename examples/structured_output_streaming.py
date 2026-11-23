import asyncio
import os
from typing import List, Literal
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

client = AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

MODEL = "claude-haiku-5-5"


# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------
class Character(BaseModel):
    name: str = Field(description="Character's name")
    role: str = Field(description="Character's role in the story")


class MovieInfo(BaseModel):
    title: str = Field(description="Movie title")
    director: str = Field(description="Director name")
    release_year: int = Field(description="Release year")
    rating: float = Field(ge=0.0, le=10.0, description="Rating out of 10")
    genre: List[str] = Field(description="List of genres")
    characters: List[Character] = Field(description="Main characters")


# ---------------------------------------------------------------------------
# Method 1: Native Streaming with output_format (Recommended)
# ---------------------------------------------------------------------------
async def stream_structured_native(prompt: str) -> MovieInfo:
    """Streams JSON tokens in real-time, then retrieves the parsed Pydantic model."""
    print("=== Method 1: Native Streaming (messages.stream + output_format) ===")
    print("Streaming tokens: ", end="", flush=True)

    async with client.messages.stream(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        output_format=MovieInfo,  # Pydantic schema
    ) as stream:

        # 1. Stream the raw JSON chunks as they arrive in real-time
        async for text_chunk in stream.text_stream:
            print(text_chunk, end="", flush=True)

        print("\n\n--- Stream Completed ---")

        # 2. Get the final parsed & validated Pydantic object
        final_message = await stream.get_final_message()
        parsed_result: MovieInfo = final_message.parsed_output
        return parsed_result


# ---------------------------------------------------------------------------
# Method 2: Tool-Call Streaming (tool_choice)
# ---------------------------------------------------------------------------
async def stream_structured_tool_choice(prompt: str) -> MovieInfo:
    """Streams tool input JSON deltas, then validates the final tool input."""
    print("\n=== Method 2: Tool Calling Stream ===")
    print("Streaming tool input deltas: ", end="", flush=True)

    tool_name = "save_movie_info"

    async with client.messages.stream(
        model=MODEL,
        max_tokens=1000,
        tools=[
            {
                "name": tool_name,
                "description": "Save movie information",
                "input_schema": MovieInfo.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:

        # Stream partial json deltas from the tool call
        async for event in stream:
            if event.type == "content_block_delta" and hasattr(event.delta, "partial_json"):
                print(event.delta.partial_json, end="", flush=True)

        print("\n\n--- Stream Completed ---")

        # Extract and validate from the final message
        final_message = await stream.get_final_message()
        for block in final_message.content:
            if block.type == "tool_use" and block.name == tool_name:
                return MovieInfo.model_validate(block.input)

    raise RuntimeError("No tool call block found in response.")


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------
async def main():
    prompt = (
        "Provide detailed information about the film 'Interstellar', "
        "including director, year, genres, rating, and main characters."
    )

    # Method 1
    result = await stream_structured_native(prompt)
    print("Final Validated Pydantic Object:")
    print(f"Title: {result.title}")
    print(f"Director: {result.director} ({result.release_year})")
    print(f"Characters: {[c.name for c in result.characters]}")

    # Method 2
    result2 = await stream_structured_tool_choice(prompt)
    print("Final Validated Pydantic Object from Tool:")
    print(f"Title: {result2.title}")
    print(f"Rating: {result2.rating}/10")


if __name__ == "__main__":
    asyncio.run(main())
