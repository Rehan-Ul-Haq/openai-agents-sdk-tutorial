import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,
    function_tool,
    enable_verbose_stdout_logging,
    ModelSettings,

)

"""
This example shows how the default behavior of 'tool_use_behavior' can be changed.
The 'stop_on_first_tool' option makes sure when tools is called, the output is not sent to LLM.
The direct result of the tool is returned to the user.
How it works?
    1. The agent calls a tool.
    2. The tool executes and returns a result.
    3. The tool result is sent back directly to user without processing.
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


class Weather(BaseModel):
    city: str
    temperature_range: str
    conditions: str

@function_tool
def get_weather(city: str) -> Weather:
    print("Weather tool called")
    return Weather(city=city, temperature_range='14 to 20 deg', conditions='sunny')


async def main():

    agent = Agent(
        name="Weather agent",
        instructions="You are a helpful agent.",
        tools=[get_weather],
        tool_use_behavior='stop_on_first_tool',
        model_settings=ModelSettings(
            tool_choice="required"
        ), 
        model=ext_model
    )

    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())