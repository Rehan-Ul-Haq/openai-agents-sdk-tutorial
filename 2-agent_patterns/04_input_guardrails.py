import os
import asyncio
from typing import Any, Literal
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,
    RunContextWrapper,
    enable_verbose_stdout_logging,
    input_guardrail,
    TResponseInputItem,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
)

"""
This example shows how to use guardrails.

Guardrails are checks that run in parallel to the agent's execution.
They can be used to do things like:
- Check if input messages are off-topic
- Check that output messages don't violate any policies
- Take over control of the agent's execution if an unexpected input is detected

In this example, we'll setup an input guardrail that trips if the user is asking to do math homework.
If the guardrail trips, we'll respond with a refusal message.
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


# Pydantic Model to get structured output from guardrail_agent
class MathHomeworkOutput(BaseModel):
    reasoning: str
    is_math_homework: bool

guardrail_agent = Agent(
    name='Guardrail Check',
    instructions="Check if the user is asking about math homework of match questions.",
    output_type=MathHomeworkOutput,
    model=ext_model
)

# Create a function which shall call input guardrail agent.
@input_guardrail
async def math_guardrail(
    context:RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """This is an input guardrail function, which happens to call an agent to check if the input
    is a math homework question.
    """
    result = await Runner.run(guardrail_agent, input, context=context.context)
    final_output = result.final_output_as(MathHomeworkOutput)
    print(f"Guardrail function final_output: {final_output}")
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=final_output.is_math_homework,
    )


async def main():
    agent = Agent(
        name="Customer support agent",
        instructions="You are a customer support agent. You help customers with their questions.",
        input_guardrails=[math_guardrail],
        model=ext_model
    )

    input_data: list[TResponseInputItem] = []

    while True:
        user_input = input("Enter a message: ")
        input_data.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        try:
            result = await Runner.run(agent, input_data)

            print(f"Input Guardrail Result: {result.input_guardrail_results}")
            print("=========================")
            print(f"Context Wrapper Result: {result.context_wrapper}")
            print("=========================")
            print(result.final_output)
            # If the guardrail didn't trigger, we use the result as the input for the next run
            input_data = result.to_input_list()
        except InputGuardrailTripwireTriggered:
            # If the guardrail triggered, we instead add a refusal message to the input
            message = "Sorry, I can't help you with your math homework."
            print(message)
            input_data.append(
                {
                    "role": "assistant",
                    "content": message,
                }
            )

    # Sample run:
    # Enter a message: What's the capital of California?
    # The capital of California is Sacramento.
    # Enter a message: Can you help me solve for x: 2x + 5 = 11
    # Sorry, I can't help you with your math homework.


if __name__ == "__main__":
    asyncio.run(main())