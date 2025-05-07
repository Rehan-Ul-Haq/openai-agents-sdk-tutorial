import os
import random
import asyncio
import logfire
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    function_tool,
    RunHooks,
    Tool,
    Usage,
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


class ExampleHook(RunHooks):
    def __init__(self):
        self.counter = 0

    def _usage_to_str(self, usage: Usage) -> str:
        print(f"Request: {usage.requests}, I/P Tokens: {usage.input_tokens}, O/P Tokens: {usage.output_tokens}, \
                Total Tokens: {usage.total_tokens}")

    async def on_agent_start(self, context: RunContextWrapper, agent: Agent):
        self.counter += 1
        print(f"Agent started: {agent.name}, Context: {context.context}, Counter: {self.counter}, Usage: {self._usage_to_str(context.usage)}")

    async def on_agent_end(self, context: RunContextWrapper, agent: Agent, output: str):
        self.counter += 1
        print(f"Agent ended: {agent.name}, Context: {context.context}, Output: {output}, Counter: {self.counter}, Usage: {self._usage_to_str(context.usage)}")

    async def on_handoff(self, context: RunContextWrapper, from_agent: Agent, to_agent: Agent):
        self.counter += 1
        print(f"Handing off from: {from_agent.name}, to: {to_agent.name}, Context: {context.context}, Counter: {self.counter}, Usage: {self._usage_to_str(context.usage)}")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool):
        self.counter += 1
        print(f"Tool started: {tool.name}, Context: {context.context}, Counter: {self.counter}, Usage: {self._usage_to_str(context.usage)}")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str):
        self.counter += 1
        print(f"Tool ended: {tool.name}, Context: {context.context}, Result: {result}, Counter: {self.counter}, Usage: {self._usage_to_str(context.usage)}")

hooks = ExampleHook()


@function_tool
def random_number(max: int) -> int:
    """Generate a random number up to max."""
    return random.randint(1, max)


@function_tool
def multiply_by_two(number: int) -> int:
    """Multiply a number by two."""
    return number * 2


class FinalResult(BaseModel):
    result: int


multiply_agent = Agent(
    name="Multiply Agent",
    instructions="Multiply the number by 2 and then return the final result.",
    tools=[multiply_by_two],
    model=ext_model,
    handoff_description="Multiply the number by 2.",
)

start_agent = Agent(
    name="Start Agent",
    instructions="Generate a random number and pass it to the multiply agent.",
    tools=[random_number],
    model=ext_model,
    handoffs=[multiply_agent],
)


async def main() -> None:
    max_number = input("Enter the maximum number: ")
    try:
        max_number = int(max_number)
    except ValueError:
        print("Invalid input. Please enter a valid integer.")
        return
    
    result = await Runner.run(
        starting_agent=start_agent,
        hooks=hooks,
        input=f"Generate a random number up to {max_number}.",
    )

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())