import os
import asyncio
from pydantic import BaseModel
from openai import AsyncOpenAI
import logfire
from dotenv import load_dotenv
from agents import (
    Agent, 
    Runner, 
    OpenAIChatCompletionsModel, 
    function_tool,
    RunConfig
)
from agents.tracing import GLOBAL_TRACE_PROVIDER
from agents import enable_verbose_stdout_logging

"""This example demostrates how to use an agent as a tool in another agent and how can we provide """

enable_verbose_stdout_logging()


# Load environment variables from .env file
load_dotenv()



# This Parameter would make sure that the openai tracing is disabled while logfire tracing would still work
GLOBAL_TRACE_PROVIDER.shutdown()

logfire.configure()
logfire.instrument_openai_agents()

# Uncommenting this would disable tracing for all tracing providers
# set_tracing_disabled(True) 

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key or not base_url or not ext_model:
    raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")

# Create an external provider
ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
model = OpenAIChatCompletionsModel(model=ext_model, openai_client=ext_client)

class TechInput(BaseModel):
    """Input for the technical support tool."""
    issue: str


@function_tool
async def run_technical_support(tech_input: TechInput) -> str:
    """A tool that runs technical support agent.
    This tool takes a technical issue as input and returns a response from the technical support agent.
    Args:
        tech_input (TechInput): The technical issue to be addressed.
    Returns:
        str: The response from the technical support agent.
    Example:
        >>> tech_input = TechInput(issue="My internet is down.")
        >>> response = await run_technical_support(tech_input)
        >>> print(response)
        "Please check your modem and router. If the issue persists, contact your ISP."
    """

    tech_agent = Agent(
    name='Technical Support Agent',
    instructions='You are a technical support agent. You can assist with technical inquiries.',
    handoff_description="Handles technical inquiries and can transfer to other agents if needed.",
    model=model,
    )

    config = RunConfig(model='gpt-4o')

    result = await Runner.run(
        starting_agent=tech_agent,
        input=tech_input.issue,
        max_turns=2,
        run_config=config
        )
    return str(result.final_output)

agent = Agent(
    name='Customer Service Agent',
    instructions=(
        'You are a customer service agent. You can assist with general inquiries.'
        'Plan your response carefully and reflect on the user\'s needs.'
        'For any technical related issues, you MUST use the technical support tool.'
        'DO NOT provide the answer directly if the user asks for technical support.'
        ),
    model=model,
    tools=[run_technical_support],
)

# Run the agent with a sample input
async def main():
    input_text = "there is a red light on my internet modem?"
    result = await Runner.run(starting_agent=agent, input=input_text, max_turns=3)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())