import os
import random
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from agents import (
    Agent,
    Runner,
    function_tool,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    enable_verbose_stdout_logging,
    set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,

)


from typing import List


"""
By default, agents produce plain text (i.e. str) outputs. 
If you want the agent to produce a particular type of output, you can use the output_type parameter.
A common choice is to use Pydantic objects, 
but we support any type that can be wrapped in a Pydantic TypeAdapter - dataclasses, lists, TypedDict, etc.
Important to note that some old models do not support structured output.

Use 'gemini-2.5-flash-preview-04-17' in env variable MODEL_NAME

"""


load_dotenv()

set_tracing_disabled(True)

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

print(ext_model)

if not api_key or not base_url or not ext_model:
    raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")

enable_verbose_stdout_logging()

ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
model = OpenAIChatCompletionsModel(model=ext_model, openai_client=ext_client)

set_default_openai_api('chat_completions')
set_default_openai_client(ext_client)

class Weather(BaseModel):   
    city: str
    temperature_range: str
    conditions: str


# @function_tool
# def get_weather(location: str) -> str:
#     """Get the current weather for a given location."""
#     # Simulate an API call to get weather data
#     return f"Weather in {location}: {random.randint(20, 30)}°C, {random.choice(['Sunny', 'Cloudy', 'Rainy'])}"


agent = Agent(
    name="WeatherAgent",
    instructions="Get the current weather for a given location.",
    # tools=[get_weather],
    model=model,
    output_type=Weather, 
)

async def main():
    # Run the agent with a sample input
    result = await Runner.run(
        starting_agent=agent,
        input="What's the weather like in Islamabad?",
    )
    print("Full Output: ", result.final_output)
    print("Parameter Output", result.final_output.city)
    print("Parameter Output", result.final_output.temperature_range)
    print("Parameter Output", result.final_output.conditions)


if __name__ == "__main__":
    asyncio.run(main())