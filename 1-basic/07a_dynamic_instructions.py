import os
import asyncio
import logfire
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_api, enable_verbose_stdout_logging, set_default_openai_client, RunContextWrapper
from agents.tracing import GLOBAL_TRACE_PROVIDER


load_dotenv()

GLOBAL_TRACE_PROVIDER.shutdown()
enable_verbose_stdout_logging()

logfire.configure()
logfire.instrument_openai_agents()


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

@dataclass
class Preferences:
    language: str
    is_formal: bool


def pref_instructions(run_context:RunContextWrapper, agent:Agent[Preferences]) -> str:
    return f"""
    You are a helpful assistant. 
    You can assist with any user inquiries. 
    Your language is {run_context.context.language} and your tone shall be {'formal' if run_context.context.is_formal else 'casual'}.
    """

async def main():
    pref = Preferences(language='Urdu', is_formal=False)

    agent = Agent(
        name='Assistant',
        instructions=pref_instructions,
        model='gemini-2.0-flash',
    )
    result = await Runner.run(
        starting_agent=agent,
        input="Draft an email to my manager about the project update.",
        context=pref,
    )

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())