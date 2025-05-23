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
This example shows how list of tools can be passed in 'tool_use_behavior'..
How it works?
When you pass a list of tool names to tool_use_behavior, the agent will:
    1. Stop running if any of the tools in the list are called.
    2. Use the output of the first matching tool call (from the list in 'tool_use_behavior') as the final output.
    3. Not process the result through the LLM.
    4. However, if any tool called not avaialble in the list, the result shall be processed through LLM.
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

class Population(BaseModel):
    city: str
    population: str

class GDP(BaseModel):
    city: str
    gdp: str

@function_tool
def get_weather(city: str) -> Weather:
    print("Weather tool called")
    return Weather(city=city, temperature_range='14 to 20 deg', conditions='sunny')

@function_tool
def get_population(city: str) -> Population:
    print("Population tool called")
    return Population(city=city, population='12 million')

@function_tool
def get_gdp(city: str) -> GDP:
    print("GDP tool called")
    return GDP(city=city, gdp='1 trillion')


async def main():

    agent = Agent(
        name="Weather agent",
        instructions="You are a helpful agent.",
        tools=[get_weather, get_population, get_gdp],
        tool_use_behavior={"stop_at_tool_names":["get_weather", "get_population"]},
        model_settings=ModelSettings(
            tool_choice="required"
        ), 
        model=ext_model
    )

    # result = await Runner.run(agent, input="What's the weather in Tokyo? and what is it's population")

    # result = await Runner.run(agent, input="What's the population in Tokyo? and how is the weather")

    # result = await Runner.run(agent, input="What is the GDP of tokyo")

    result = await Runner.run(agent, input="What is the GDP of Tokyo and what is its population")

    print(f"Final Output: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())