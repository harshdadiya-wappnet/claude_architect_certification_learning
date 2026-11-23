
import os
import asyncio
from dotenv import load_dotenv
from anthropic import AsyncAnthropic

load_dotenv()

# Initialize async Anthropic client
client = AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 200

SYSTEM_PROMPT = """
You are a helpful AI assistant.
Keep your responses concise and informative.
"""


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


async def chat_with_model(
    messages,
    model=MODEL,
    max_tokens=MAX_TOKENS
):
    response_text = ""

    try:
        async with client.messages.stream(
            system=SYSTEM_PROMPT,
            model=model,
            max_tokens=max_tokens,
            messages=messages,
        ) as stream:

            async for text in stream.text_stream:
                print(text, end="", flush=True)
                response_text += text

        return response_text

    except Exception as e:
        print(f"\nError: {e}")
        return None


async def main():

    # Maintain conversation history
    messages = []

    print("Claude Chat")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:

        user_input = await asyncio.to_thread(input, "You: ")

        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not user_input.strip():
            continue

        add_user_message(messages, user_input)

        print("Assistant: ", end="", flush=True)

        response = await chat_with_model(messages)

        if response is not None:
            # Store complete assistant response
            add_assistant_message(messages, response)

        print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nChat interrupted.")
