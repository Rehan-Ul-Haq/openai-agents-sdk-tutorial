"""Example  with non-strict mode with Custom Output Schema"""

import os
import json
import random
import asyncio
from typing import Any
import logfire
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    function_tool,
    HandoffInputData,
    handoff,
    trace,

)
from agents.extensions import handoff_filters
from agents.tracing import GLOBAL_TRACE_PROVIDER



load_dotenv()

GLOBAL_TRACE_PROVIDER.shutdown()
logfire.configure()
logfire.instrument_openai_agents()

# set_tracing_disabled(True)

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key or not base_url or not ext_model:
    raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")


# Create an external provider
ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)


ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')


@function_tool
def random_number_tool(max: int) -> int:
    """Generate a random number between 1 and max."""
    return random.randint(1, max)



def spanish_handoff_message_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    """Filter the handoff messages to Spanish Agent."""
    # First, remove any tool-related message from the message history.
    handoff_message_data = handoff_filters.keep_last_n_items(handoff_message_data, 50, keep_tool_messages=False)
    return handoff_message_data

first_agent = Agent(
    name="Assistant",
    instructions="Be extremely concise.",
    tools=[random_number_tool],
    model=ext_model,
)

spanish_agent = Agent(
    name="Spanish Assistant",
    instructions="You only speak Spanish and are extremely concise.",
    handoff_description="A Spanish-speaking assistant.",
    model=ext_model,
)

second_agent = Agent(
    name="Assistant",
    instructions=(
        "Be a helpful assistant. If the user speaks Spanish, handoff to the Spanish assistant."
    ),
    handoffs=[handoff(spanish_agent, input_filter=spanish_handoff_message_filter)],
    model=ext_model,
)


async def main():
    # Trace the entire run as a single workflow
    with trace(workflow_name="Message filtering"):
        # 1. Send a regular message to the first agent
        result = await Runner.run(first_agent, input="Hi, my name is Sora.")

        print("Step 1 done")

        # 2. Ask it to generate a number
        result = await Runner.run(
            first_agent,
            input=result.to_input_list()
            + [{"content": "Can you generate a random number between 0 and 100?", "role": "user"}],
        )

        print("Step 2 done")

        # 3. Call the second agent
        result = await Runner.run(
            second_agent,
            input=result.to_input_list()
            + [
                {
                    "content": "I live in New York City. Whats the population of the city?",
                    "role": "user",
                }
            ],
        )

        print("Step 3 done")

        # 4. Cause a handoff to occur
        result = await Runner.run(
            second_agent,
            input=result.to_input_list()
            + [
                {
                    "content": "Por favor habla en español. ¿Cuál es mi nombre y dónde vivo?",
                    "role": "user",
                }
            ],
        )

        print("Step 4 done")

    print("\n===Final messages===\n")

    # 5. That should have caused spanish_handoff_message_filter to be called, which means the
    # output should be missing the first two messages, and have no tool calls.
    # Let's print the messages to see what happened
    for message in result.to_input_list():
        print(json.dumps(message, indent=2))

if __name__ == "__main__":
    asyncio.run(main())