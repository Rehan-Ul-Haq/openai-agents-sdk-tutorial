"""
This is a simple chat agent that uses OpenAI's GPT-3.5 model to respond to queries.
Tracing can be disabled by uncommenting the set_tracing_disabled line.
"""

import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.tracing import set_tracing_disabled


# Load environment variables from .env file
load_dotenv()


# Uncomment the following line to disable tracing
# set_tracing_disabled(disabled=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Please set it in your .env file.")

agent = Agent(
    name="simple_chat_agent",
    tools=[],
    model="gpt-3.5-turbo",
)

async def main():
    # Run the agent with a simple prompt
    response = await Runner.run(
        starting_agent=agent,
        input="What is the capital of France?",
    )
    print(response.final_output)


if __name__ == "__main__":
    asyncio.run(main())