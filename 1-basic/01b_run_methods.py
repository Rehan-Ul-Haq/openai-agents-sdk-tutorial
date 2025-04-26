import os
import asyncio
import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.tracing import set_tracing_disabled
from openai.types.responses import ResponseTextDeltaEvent
from agents.tracing import GLOBAL_TRACE_PROVIDER


# Load environment variables from .env file
load_dotenv()
GLOBAL_TRACE_PROVIDER.shutdown()

logfire.configure()
logfire.instrument_openai_agents()

provider = input("Choose LLM provider ('openai' or 'gemini'): ").strip().lower()

if provider not in ["openai", "gemini"]:
    raise ValueError("Invalid provider. Please choose 'openai' or 'gemini'.")
elif provider == "openai":
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Please set it in your .env file.")
    selected_model="gpt-3.5-turbo",


elif provider == "gemini":
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("BASE_URL")
    ext_model = os.getenv("MODEL_NAME")
    if not api_key or not base_url or not ext_model:
        raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")
    ext_client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    selected_model = OpenAIChatCompletionsModel(
        model=ext_model,
        openai_client=ext_client,
    )

agent = Agent(
    name="simple_chat_agent",
    tools=[],
    model=selected_model,
)

def main_sync():
    prompt = input("Enter your prompt: ")
    response = Runner.run_sync(
        starting_agent=agent,
        input=prompt,
    )
    print(response.final_output)


async def main_async():
    prompt = input("Enter your prompt: ")
    response = await Runner.run(
        starting_agent=agent,
        input=prompt,
    )
    print(response.final_output)

async def main_streaming():
    prompt = input("Enter your prompt: ")
    result = Runner.run_streamed(starting_agent=agent, input=prompt)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)


if __name__ == "__main__":
    operation = input("Enter the run mode (e.g., 'sync', 'async', 'streaming'): ").strip().lower()
    if operation not in ["sync", "async", "streaming"]:
        raise ValueError("Invalid operation. Please type 'sync', 'async', or 'streaming'.")
    if operation == 'sync':
        main_sync()
    elif operation == 'async':
        asyncio.run(main_async())
    elif operation == 'streaming':
        asyncio.run(main_streaming())
