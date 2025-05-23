import os
import asyncio
import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool
from agents.tracing import set_tracing_disabled
from agents.tracing import GLOBAL_TRACE_PROVIDER


# Check the logfire version
print(logfire.__version__)

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

# Create a function tool
@function_tool
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

# Create an agent with the external provider and function tool
agent = Agent(
    name='Math Agent',
    instructions='You are a math agent. You can add numbers using the add function.',
    model=model,
    tools=[add]
)

# Run the agent with a sample input
async def main():
    input_text = "What is 8 + 3?"
    result = await Runner.run(starting_agent=agent, input=input_text)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())