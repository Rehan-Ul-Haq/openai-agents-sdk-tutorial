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
    )
from typing import List
from agents.extensions.models.litellm_model import LitellmModel


"""
This example explains the concept that tools can be called multiple times in a single agent run.
It demonstrates how a tool is called multiple times in a single agent run.
We shall use this example with openai models as gemini models (Vertex AI) 
do not support function calling and output time simultaneously.
"""


load_dotenv()

# api_key = os.getenv("GEMINI_API_KEY")
# base_url = os.getenv("BASE_URL")
# ext_model = os.getenv("MODEL_NAME")

# if not api_key or not base_url or not ext_model:
#     raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")

enable_verbose_stdout_logging()
set_default_openai_api('chat_completions')
set_tracing_disabled(True)

# ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
# model = OpenAIChatCompletionsModel(model=ext_model, openai_client=ext_client)

class Weather(BaseModel):   
    city: str
    temperature_range: str
    conditions: str

class WeatherData(BaseModel):
    weather: List[Weather]


@function_tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    # Simulate an API call to get weather data
    return f"Weather in {location}: {random.randint(20, 30)}°C, {random.choice(['Sunny', 'Cloudy', 'Rainy'])}"


agent = Agent(
    name="WeatherAgent",
    instructions="Get the current weather for a given location.",
    tools=[get_weather],
    # model=model,  
    # model=LitellmModel(model=ext_model, api_key=api_key),
    model='gpt-4o',
    output_type=WeatherData, 
    
)

async def main():
    # Run the agent with a sample input
    result = await Runner.run(
        starting_agent=agent,
        input="What's the weather like in Lahore, Karachi, Islamabad?",
    )
    # print("Full Output: ", result.final_output)
    # print("Parameter Output", result.final_output.weather)
    for _ in result.final_output.weather:
        print("City: ", _.city)
        print("Temperature Range: ", _.temperature_range)
        print("Conditions: ", _.conditions)
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())