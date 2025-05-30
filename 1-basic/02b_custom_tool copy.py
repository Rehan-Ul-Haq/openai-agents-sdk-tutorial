import os
import asyncio
import json
from typing import Any
from openai import AsyncOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, FunctionTool, OpenAIChatCompletionsModel, RunContextWrapper, Runner, function_tool, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from agents import enable_verbose_stdout_logging

# Enables verbose logging to stdout (our terminal). This is useful for debugging.
enable_verbose_stdout_logging()


# Load environment variables from .env file
load_dotenv()

load_dotenv()

set_tracing_disabled(True)

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key or not base_url or not ext_model:
    raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")

ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
model = OpenAIChatCompletionsModel(model=ext_model, openai_client=ext_client)

set_default_openai_api('chat_completions')
set_default_openai_client(ext_client)

# class Weather(BaseModel):
#     city: str
#     temperature_range: str
#     conditions: str


# Define the simple weather search tool
# @function_tool(name_override="definitely_get_weather")
# def get_weather(city: str) -> Weather:
#     """Get the weather for a given city.
#     This function takes a city name as input and returns a Weather object with the city's weather information.

#     Args:
#         city (str): The name of the city to get the weather for.

#     Returns:
#         Weather: A Weather object containing the weather information for the specified city.

#     Example:
#         >>> weather = get_weather("New York")
#         >>> print(weather)
#         Weather(city='New York', temperature_range='14-20C', conditions='Sunny with wind.')
#     """
#     print("[debug] get_weather called")
#     return Weather(city=city, temperature_range="14-20C", conditions="Sunny with wind.")

# Define the a custom tool for getting weather information

class FunctionArgs(BaseModel):
    citt: str # This error is intentional to demonstrate error handling in the tool

def get_weather(city: str) -> str:
    return f"Weather in {city}: 14 to 20, Sunny with wind."

async def run_function(ctx: RunContextWrapper[Any], args: str) -> str:
    try:
        # Parse the JSON string into a Pydantic model
        print(f"[debug] run_function called with args: {args}")
        parsed_args = FunctionArgs.model_validate_json(args)
        return get_weather(parsed_args.city)
    except Exception as e:
        print(f"[error] Failed to parse arguments: {e}")
        return "Error: Invalid arguments provided."

custom_tool = FunctionTool(
    name="get_weather",
    description="Get the weather for a given city.",
    params_json_schema=FunctionArgs.model_json_schema(), # json schema for the arguments (a python dictionary)
    on_invoke_tool= run_function,
)


# Define the agent with the weather search tool
agent = Agent(
    name="WeatherAgent",
    instructions="Use the weather search tool to find the weather in a specific location.",
    model=ext_model,
    tools=[custom_tool],
)

# for tool in agent.tools:
#     print(f"Tool Name: {tool.name}, Description: {tool.description}")
#     print(f"Tool Params JSON Schema: {tool.params_json_schema}")
#     print(type(tool.params_json_schema))
#     print(f"Args:::: {json.dumps(tool.params_json_schema, indent=2)}")


# Run the agent with a sample input
async def main():
    input_text = "What's the weather like in New York?"
    result = await Runner.run(agent, input_text)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
