import os
import random
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner, function_tool
from typing import List


load_dotenv()

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
    model="gpt-4o-mini",  # gpt-3.5-turbo is not supported for structured output
    output_type=WeatherData, # Important to note that some old models do not support structured output
)

async def main():
    # Run the agent with a sample input
    result = await Runner.run(
        starting_agent=agent,
        input="What's the weather like in Lahore, Karachi, Islamabad?",
    )
    print("Full Output: ", result.final_output)
    # print("Parameter Output", result.final_output.location)


if __name__ == "__main__":
    asyncio.run(main())