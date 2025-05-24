from __future__ import annotations
import os
import asyncio
import logfire
from dotenv import load_dotenv
from agents import (
    Agent, 
    Runner, 
    AsyncOpenAI, 
    OpenAIChatCompletionsModel,
    set_default_openai_client,
    set_default_openai_api,
)
from agents.tracing import GLOBAL_TRACE_PROVIDER
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


# Load environment variables from .env file
load_dotenv()

# This Parameter would make sure that the openai tracing is disabled while logfire tracing would still work
GLOBAL_TRACE_PROVIDER.shutdown()

logfire.configure()
logfire.instrument_openai_agents()

# Uncommenting this would disable tracing for all tracing providers
# set_tracing_disabled(True) 

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key or not base_url or not ext_model:
    raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")

# Create an external provider
ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')


# Create an agent with the external provider and function tool
billing_agent = Agent(
    name='Billing Support Agent',
    instructions='You are a billing support agent. You can assist with billing inquiries.',
    handoff_description="Handles billing inquiries.",
    model='gemini-2.0-flash'
    )

tech_agent = Agent(
    name='Technical Support Agent',
    instructions='You are a technical support agent. You can assist with technical inquiries.',
    handoff_description="Handles technical inquiries.",
    model='gemini-2.0-flash'
    )

agent = Agent(
    name='Customer Service Agent',
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        'You are a customer service agent. You can assist with general inquiries.'
        'If the inquiry is related to billing, transfer it to the Billing Support Agent.'
        'If the inquiry is related to technical support, transfer it to the Technical Support Agent.'
        ),
    model=OpenAIChatCompletionsModel(
        model=ext_model, openai_client=ext_client
        ),
    handoffs=[billing_agent, tech_agent],
)

# Run the agent with a sample input
async def main():
    input_text = "The power light on my internet router is blinking red. What should I do?"
    result = await Runner.run(starting_agent=agent, input=input_text)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())