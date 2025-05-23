import os
import asyncio
from typing import Any, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,
    RunContextWrapper,
    enable_verbose_stdout_logging,
    output_guardrail,
    TResponseInputItem,
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
)

"""
This example shows how to use output guardrails.

Output guardrails are checks that run on the final output of an agent.
They can be used to do things like:
- Check if the output contains sensitive data
- Check if the output is a valid response to the user's message

In this example, we'll use a (contrived) example where we check if the agent's response contains
a phone number.
"""


load_dotenv()

set_tracing_disabled(True)

enable_verbose_stdout_logging()

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key and not base_url and not ext_model:
    raise ValueError ("Please make sure to provide GEMINI_API_KEY, BASE_URL and MODEL_NAME.")


ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')


# This is agent's output
class MessageOutput(BaseModel):
    response: str

# Guardrail Output
class MathOutput(BaseModel):
    reasoning: str
    is_math: bool

guardrail_agent = Agent(
    name='Guardrail Check',
    instructions="Check if the output contains any math.",
    output_type=MathOutput,
    model=ext_model
)

# Create a function which shall call input guardrail agent.
@output_guardrail
async def math_guardrail(
    ctx:RunContextWrapper[None], agent: Agent, output: MessageOutput
) -> GuardrailFunctionOutput:
    """This is an output guardrail function, which happens to call an agent to check if the output
    contains any math.
    """
    result = await Runner.run(guardrail_agent, output.response, context=ctx.context)
    final_output = result.final_output_as(MathOutput)
    print(f"Guardrail function final_output: {final_output}")
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=result.final_output.is_math,
    )


agent = Agent( 
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    output_guardrails=[math_guardrail],
    output_type=MessageOutput,
    model=ext_model
)

async def main():
    # This should trip the guardrail
    try:
        await Runner.run(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
        print("Guardrail didn't trip - this is unexpected")

    except OutputGuardrailTripwireTriggered:
        print("Math output guardrail tripped")


if __name__ == "__main__":
    asyncio.run(main())