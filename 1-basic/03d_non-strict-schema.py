"""Example  with non-strict mode"""

import os
import asyncio
import logfire
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    function_tool,
    AgentOutputSchema,
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

# For this demo, we are using openai model with Responses API because chat completions API still gives error with non-strict mode.
# =========================================================
# Create an external provider
ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)


ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')

#==========================================================

"""
Earlier, we saw with Strict JSON schema enabled but the output type generated was not JSON-compatible 
due to which the validation was failing.
The error suggested that either make the output type strict, 
or pass output_schema_strict=False to your Agent(). But let's  assume, 
our use case requires the OutputType which we defined. 
So we have to pass the output_schema_strict=False to the Agent() to make it non-strict. 
This will allow the model to output a dictionary with integer keys, 
and the agent will still be able to parse it correctly.

**Note**: If we use external provider (gemini), we would get an `BadRequestError` error form API.
"""

# Here we define a schema for the output which is not JSON-compatible.
@dataclass
class OutputType:
    jokes: dict[int, str]
    """A list of jokes, indexed by joke number."""


async def main():
    # Now wrap the dataclass(OutputType) in `AgentOutputSchema` with strict mode turned off.
    # Now the agent is allowed to produce output that might not be perfectly valid JSON (it won’t enforce all JSON schema rules).
    agent = Agent(
        name="Assistant",
        instructions="You're a helpful assistant.",
        model=ext_model,
        output_type=OutputType,
    )

    input = "Tell me 3 short jokes"
    agent.output_type = AgentOutputSchema(OutputType, strict_json_schema=False)

    # Run the agent with non-strict JSON schema
    result = await Runner.run(agent, input)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())