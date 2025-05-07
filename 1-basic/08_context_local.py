import os
import asyncio
import logfire
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel, set_default_openai_api, enable_verbose_stdout_logging, set_default_openai_client, RunContextWrapper
from agents.tracing import GLOBAL_TRACE_PROVIDER


load_dotenv()

GLOBAL_TRACE_PROVIDER.shutdown()
enable_verbose_stdout_logging()

logfire.configure()
logfire.instrument_openai_agents()


api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key or not base_url or not ext_model:
    raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")


# Create an external provider
ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)


ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')



@dataclass
class UserContext:
    user_id: str


# Mock Db call
PREFERENCES_DB = {
    "user123": "english",
    "user456": "urdu",
    "user789": "spanish",
}

# Tool to fetch user preferences from a mock database
@function_tool
def get_user_preferences(wrapper: RunContextWrapper[UserContext]) -> str:
    """
    Tool to fetch the user's preferred language.
    """
    user_id = wrapper.context.user_id
    # Fetch preference, default to 'pashtu' if not found
    return PREFERENCES_DB.get(user_id, "pashtu")


async def main():

    user_info = UserContext(user_id="user789")


    agent = Agent[UserContext](
    name='Assistant',
    instructions="You're a helpful assistant and assist with user inquiries in their preferred language by using the get_user_preferences tool.",
    tools=[get_user_preferences],
    model='gemini-2.0-flash', # gemini-2.0-flash is not calling the function
    # model='gemini-2.5-flash-preview-04-17',
)
    result = await Runner.run(
        starting_agent=agent,
        input="Draft an email to my manager about the project update.",
        context=user_info,
    )

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())