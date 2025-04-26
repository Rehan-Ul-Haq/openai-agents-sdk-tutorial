import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner, function_tool


load_dotenv()

class WeatherData(BaseModel):
    location: str
    temperature: float
    condition: str


@function_tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    # Simulate an API call to get weather data
    return f"Weather in {location}: 25°C, Sunny"


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
        input="What's the weather like in New York?",
    )
    print("Full Output", result.final_output)
    print("Parameter Output", result.final_output.location)


if __name__ == "__main__":
    asyncio.run(main())