"""Basic example of using a non-strict schema with Gemini API."""

import os
import asyncio
import logfire
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
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
By default, LLMs generate plain text. However, the models can be guided to output JSON. 
This is done by specifying a schema for the output. 
As we said earlier, we create a schema and pass that schema to the agent through 'output_type' parameter. This approach ensures that the model's output not only is valid JSON but also conforms to the specified schema,
which is crucial for applications requiring structured data.  

This example shows how to handle agent outputs that don't fit the standard JSON schema. Normally, OpenAI Agents enforce a **strict JSON schema** for outputs (so the model's reply is valid JSON). But some Python types (like a `dict[int, ...]` or custom formats) are not strictly JSON-friendly. A dictionary with integer keys, for example, is not valid JSON. In this case, we can use a **non-strict schema** to allow the model to output a dictionary with integer keys.
This is done by using the `AgentOutputSchema` class, which allows for a more flexible schema definition. The model can then output a dictionary with integer keys, and the agent will still be able to parse it correctly.

"""

# Here we define a schema for the output which is not JSON-compatible.
@dataclass
class OutputType:
    """A list of jokes, indexed by joke number."""
    jokes: dict[int, str]


async def main():
    agent = Agent(
        name="Assistant",
        instructions="You're a helpful assistant.",
        model=ext_model,
        output_type=OutputType
    )

    input = "Tell me 3 short jokes"

    # UserError exceptions is raised when the output type is not valid JSON.
    # If not handled, this will cause the application to crash.
    # We shall handle this exception gracefully and print the error message.

    try:
        # Run the agent with strict JSON schema
        """We shall get the following error. Error: Strict JSON schema is enabled, but the output type is not valid. Either make the output type strict, or pass output_schema_strict=False to your Agent()"""
        result = await Runner.run(starting_agent=agent, input=input)
        print(f"Result: {result.final_output}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())