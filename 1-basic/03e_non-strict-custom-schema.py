"""Example  with non-strict mode with Custom Output Schema"""

import os
import json
import asyncio
from typing import Any
import logfire
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    AgentOutputSchemaBase,
    set_default_openai_api,
    set_default_openai_client,

)
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


"""
Now we define a custom output schema by subclassing `AgentOutputSchemaBase`.
This allows us to define a schema that is not strictly JSON-compatible. 
"""

# Here we define a schema for the output which is not JSON-compatible.
@dataclass
class OutputType:
    jokes: dict[int, str]
    """A list of jokes, indexed by joke number."""


# Custom output schema class
class CustomOutputSchema(AgentOutputSchemaBase):
    """A demonstration of a custom output schema."""

    def is_plain_text(self) -> bool:
        return False

    def name(self) -> str:
        return "CustomOutputSchema"

    def json_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"jokes": {"type": "object", "properties": {"joke": {"type": "string"}}}},
        }

    def is_strict_json_schema(self) -> bool:
        return False

    def validate_json(self, json_str: str) -> Any:
        json_obj = json.loads(json_str)
        print("Debug: JSON object:", json_obj)
        # Just for demonstration, we'll return a list.
        return list(json_obj["jokes"].values())


async def main():
    # """Now wrap the dataclass(OutputType) in `AgentOutputSchema` with strict mode turned off.
    # Now the agent is allowed to produce output that might not be perfectly valid JSON (it won’t enforce all JSON schema rules)."""
    agent = Agent(
        name="Assistant",
        instructions="You're a helpful assistant.",
        model=ext_model,
        output_type=OutputType,
    )

    input = "Tell me 3 short jokes about cats."
    agent.output_type = CustomOutputSchema()

    """
    Here are important points to note:
    1. With external model (Gemini-2.0-flash), we get a single joke despite 3 jokes in query.
    2. With openai default model (gpt-4o), we get 3 jokes.
    """

    # Run the agent with non-strict JSON schema
    result = await Runner.run(agent, input)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())