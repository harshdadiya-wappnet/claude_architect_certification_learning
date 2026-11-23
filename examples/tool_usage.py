
import os
import asyncio
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from anthropic.types import ToolParam

load_dotenv()

client = AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 200
MAX_TOOL_ROUNDS = 10

SYSTEM_PROMPT = """
You are a helpful AI assistant.
Keep your responses concise and informative.
Use available tools whenever required.
"""

# --------------------------------------------------
# Tool functions
# --------------------------------------------------

def get_weather_info(location: str) -> str:
    """Fetch weather information for a location."""
    return (
        f"The current weather in {location} "
        "is sunny with a temperature of 25°C."
    )


# --------------------------------------------------
# Tool schemas
# --------------------------------------------------

get_weather_info_schema = ToolParam(
    {
        "name": "get_weather_info",
        "description": "Fetches the current weather information for a given location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to fetch weather information for."
                }
            },
            "required": ["location"]
        }
    }
)


# --------------------------------------------------
# Tool registry
# --------------------------------------------------

TOOL_FUNCTIONS = {
    "get_weather_info": get_weather_info
}

TOOLS = [
    get_weather_info_schema
]


# --------------------------------------------------
# Message helpers
# --------------------------------------------------

def add_user_message(messages, content):
    messages.append({
        "role": "user",
        "content": content
    })


def add_assistant_message(messages, content):
    messages.append({
        "role": "assistant",
        "content": content
    })


# --------------------------------------------------
# Tool execution
# --------------------------------------------------

async def execute_tool(tool_name, tool_input):

    print(f"\n[Tool Call] {tool_name}")
    print(f"[Tool Input] {tool_input}")

    tool_function = TOOL_FUNCTIONS.get(tool_name)

    if not tool_function:
        return f"Error: Unknown tool '{tool_name}'"

    try:
        # Run synchronous tool function without blocking
        result = await asyncio.to_thread(
            tool_function,
            **tool_input
        )

        print(f"[Tool Result] {result}\n")

        return str(result)

    except Exception as e:
        error = f"Tool execution failed: {str(e)}"
        print(error)
        return error


# --------------------------------------------------
# Streaming agent loop
# --------------------------------------------------

async def chat_with_model(
    messages,
    model=MODEL,
    max_tokens=MAX_TOKENS
):

    tool_rounds = 0

    try:

        while True:

            # Request Claude response
            async with client.messages.stream(
                system=SYSTEM_PROMPT,
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                tools=TOOLS,
            ) as stream:

                # Stream generated text
                async for text in stream.text_stream:
                    print(text, end="", flush=True)

                # Get complete response including tool_use blocks
                response = await stream.get_final_message()

            # Store complete assistant response
            add_assistant_message(
                messages,
                response.content
            )

            # Check whether Claude wants to execute tools
            if response.stop_reason != "tool_use":
                break

            tool_rounds += 1

            if tool_rounds > MAX_TOOL_ROUNDS:
                print("\nMaximum tool execution rounds reached.")
                break

            # Collect tool results
            tool_results = []

            for block in response.content:

                if block.type != "tool_use":
                    continue

                # Execute requested tool
                result = await execute_tool(
                    tool_name=block.name,
                    tool_input=block.input
                )

                # Prepare tool result block
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

            # Send tool results back to Claude
            add_user_message(
                messages,
                tool_results
            )

            # Loop again so Claude can process tool results
            print("Assistant: ", end="", flush=True)

    except Exception as e:
        print(f"\nError: {e}")


# --------------------------------------------------
# Main chat loop
# --------------------------------------------------

async def main():

    messages = []

    print("Claude Chat")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:

        user_input = await asyncio.to_thread(
            input,
            "You: "
        )

        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not user_input.strip():
            continue

        add_user_message(messages, user_input)

        print("Assistant: ", end="", flush=True)

        await chat_with_model(messages)

        print("\n")


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nChat interrupted.")
