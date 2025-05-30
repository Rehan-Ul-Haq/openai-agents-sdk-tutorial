import os
import time
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import (
    Agent,
    ModelSettings,
    RunConfig,
    Runner,
    set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,
    ItemHelpers,
    MessageOutputItem,
    enable_verbose_stdout_logging,
    function_tool


)
from agents.tracing import GLOBAL_TRACE_PROVIDER
import logfire

"""
This example shows the agents-as-tools pattern. The frontline agent receives a user message and
then picks which agents to call, as tools. In this case, it picks from a set of translation
agents.
"""


load_dotenv()

# set_tracing_disabled(True)

@function_tool
async def translate_to_spanish(text: str) -> str:
    await asyncio.sleep(3)
    return f"I have translated the text to Spanish: {text} in Spanish"


@function_tool
async def translate_to_french(text: str) -> str:
    await asyncio.sleep(4)
    return f"I have translated the text to French: {text} in French"

@function_tool
async def translate_to_italian(text: str) -> str:
    await asyncio.sleep(5)
    return f"I have translated the text to Italian: {text} in Italian"


GLOBAL_TRACE_PROVIDER.shutdown()

logfire.configure()
logfire.instrument_openai_agents()


enable_verbose_stdout_logging()

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")


if not api_key and not base_url and not ext_model:
    raise ValueError ("Please make sure to provide GEMINI_API_KEY, BASE_URL and MODEL_NAME.")


ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')


# Let's create our agents


orchestrator_agent = Agent(
    name='orchestrator_agent',
    instructions=(
        "You are a translation agent. You use the tools given to you to translalte. "
        "If asked for multiple translation, you call the relevant tools in order. "
        "You never translate on your own. You always use the provided tools to translate."
        "Before calling the tools, you inspect the user message and decide which tool to call. "
        "Do not call the tools if you're not sure about the language to translate to. "
        "If you are not sure about the language, ask the user to clarify. "

    ),
    tools=[
        translate_to_spanish,
        translate_to_french,
        translate_to_italian
    ],
    model=ext_model,
    # model='gpt-4o-mini',
    # model_settings=ModelSettings(parallel_tool_calls=True)
)

def main():
    input_prompt = input("What would you like to be translated? ")
    orchestrator_result = Runner.run_sync(
        starting_agent=orchestrator_agent,
        input=input_prompt,
    )

    print(f"Orchestrator result: {orchestrator_result.final_output}")





if __name__ == '__main__':
    # asyncio.run(main())
    main()