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
    function_tool,
    RunContextWrapper,
    FunctionToolResult,
    ToolsToFinalOutputResult,
    ModelSettings,
    enable_verbose_stdout_logging,

)

"""
This example shows how we can add custom behavior in 'tool_use_behavior'. We can create our own custom behavior by defining a function that:
    1. Receives the tool results.
    2. Processes them as needed.
    3. Returns a final output.  
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

# This function is used as a custom
async def custom_tool_use_behavior(
        context: RunContextWrapper[Any],
        results: list[FunctionToolResult]

) -> ToolsToFinalOutputResult:
    weather: Weather = results[0].output
    return ToolsToFinalOutputResult(is_final_output=True, final_output=f"{weather.city} is {weather.conditions}")


async def main():
 
    agent = Agent(
        name="Weather agent",
        instructions="You are a helpful agent.",
        tools=[get_weather],
        tool_use_behavior=custom_tool_use_behavior,
        model_settings=ModelSettings(
            tool_choice="required" 
        ),
        model=ext_model
    )

    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())