# from __future__ import annotations
import os
import asyncio
import logfire
from dotenv import load_dotenv
from agents import (
    Agent, 
    Runner, 
    AsyncOpenAI, 
    OpenAIChatCompletionsModel,
    ModelProvider,
    RunConfig
)
from agents.tracing import  GLOBAL_TRACE_PROVIDER
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



# Create an agent with the external provider and function tool
billing_agent = Agent(
    name='Billing Support Agent',
    instructions='You are a billing support agent. You can assist with billing inquiries.',
    handoff_description="Handles billing inquiries.",
    )

tech_agent = Agent(
    name='Technical Support Agent',
    instructions='You are a technical support agent. You can assist with technical inquiries.',
    handoff_description="Handles technical inquiries.",
    )

agent = Agent(
    name='Customer Service Agent',
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        'You are a customer service agent. You can assist with general inquiries.'
        'If the inquiry is related to billing, transfer it to the Billing Support Agent.'
        'If the inquiry is related to technical support, transfer it to the Technical Support Agent.'
        ),
    handoffs=[billing_agent, tech_agent],
)

"""
We define a CustomModelProvider class that inherits from ModelProvider. 
This class implements the get_model method, which is responsible 
for returning the appropriate model instance of (Model) based on the provided model name.

"""

# Here we can get model name from environment variable or user input
# The current run shall run with this specific model name. 
user_model_name = input("Enter the model name and press Enter: ")

class CustomModelProvider(ModelProvider):
    def get_model(self, model_name:str):
        """"Get the model from the external provider."""
        # We can read it from an environment variable, prompt the user, or determine it based on the application logic.  
        return OpenAIChatCompletionsModel(model=model_name or ext_model, openai_client=ext_client)

CUSTOM_MODEL_PROVIDER = CustomModelProvider()

config = RunConfig(model=user_model_name, model_provider=CUSTOM_MODEL_PROVIDER)

# Run the agent with a sample input
async def main():
    input_text = "I got charged twice for my subscription. Can you help me with this?"
    result = await Runner.run(starting_agent=agent, input=input_text, run_config=config)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())