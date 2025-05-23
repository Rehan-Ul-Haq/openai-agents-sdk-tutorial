"""
This example to provide a simple get_weather function as a tool for an agent.
Creating pydantic model for validation is optional but recommended.
The option 'enable_verbose_stdout_logging' is used to enable verbose logging for debugging purposes.
"""
import os
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()


# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Please set it in your .env file.")

class Weather(BaseModel):
    city: str
    temperature_range: str
    conditions: str


# Define the simple weather search tool
@function_tool
def get_weather(city: str) -> Weather:
    """
    Get the weather for a given city.
    Args:
        city (str): The name of the city to get the weather for.
    """
    print("[debug] get_weather called")
    return Weather(city=city, temperature_range="14-20C", conditions="Sunny with wind.")


# Define the agent with the weather search tool
agent = Agent(
    name="WeatherAgent",
    instructions="Use the weather search tool to find the weather in a specific location.",
    model="gpt-3.5-turbo",
    tools=[get_weather],
)

# Run the agent with a sample input
async def main():
    input_text = "What's the weather like in New York?"
    result = await Runner.run(agent, input_text)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
