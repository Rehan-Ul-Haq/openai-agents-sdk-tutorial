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

# The below parameter is important here. If we don't use it, tech agent would use default Responses API
# Mixing ResponsesAPI with ChatCompletion API would generate error.
# Therefore, we need to set the chat_completions api as default for all agents.
set_default_openai_api("chat_completions")

# Create an agent with the external provider and function tool
billing_agent = Agent(
    name='Billing Support Agent',
    instructions='You are a billing support agent. You can assist with billing inquiries.',
    handoff_description="Handles billing inquiries and can transfer to other agents if needed.",
    model=OpenAIChatCompletionsModel(
        model='gemini-2.0-flash', openai_client=ext_client
        )
    )
tech_agent = Agent(
    name='Technical Support Agent',
    instructions='You are a technical support agent. You can assist with technical inquiries.',
    handoff_description="Handles technical inquiries and can transfer to other agents if needed.",
    model='gpt-4o-mini'
    )

agent = Agent(
    name='Customer Service Agent',
    instructions=(
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
    input_text = "Will i get charged for the service?"
    result = await Runner.run(starting_agent=agent, input=input_text)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())