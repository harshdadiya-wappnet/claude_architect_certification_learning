"""
Task 1.2: coordinator with subagents (CLI entry point).

Run from the repo root (the imports are absolute, so use -m, not a file path):

    python -m tasks.agentic_architecture_and_orchastration.task_1_2.main

Needs ANTHROPIC_API_KEY in .env. Type 'exit' or 'quit' to stop.
"""
import asyncio

from tasks.agentic_architecture_and_orchastration.task_1_2.coordinator import run_coordinator

SAMPLES = "tasks/agentic_architecture_and_orchastration/task_1_2/samples"


async def main():
    print("Coordinator with subagents (task 1.2)")
    print("Try (full pipeline):")
    print(f"  Read {SAMPLES}/q3_sales.txt and {SAMPLES}/pricing_notes.txt, compute total revenue")
    print("  and the break-even prices, then summarise.")
    print("Try (minimal):  What is 15% of 2480?")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        request = await asyncio.to_thread(input, "Request: ")

        if request.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        if not request.strip():
            continue

        try:
            answer = await run_coordinator(request)
            print(f"\n=== Answer ===\n{answer}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
