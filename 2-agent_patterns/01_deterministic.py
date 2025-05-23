import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,

)

"""
This example demonstrates a deterministic flow, where each step is performed by an agent.
1. The first agent generates a story outline
2. We feed the outline into the second agent
3. The second agent checks if the outline is good quality and if it is a scifi story
4. If the outline is not good quality or not a scifi story, we stop here
5. If the outline is good quality and a scifi story, we feed the outline into the third agent
6. The third agent writes the story
"""


load_dotenv()

set_tracing_disabled(True)

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key and not base_url and not ext_model:
    raise ValueError ("Please make sure to provide GEMINI_API_KEY, BASE_URL and MODEL_NAME.")


ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')


# Let's create our agents
story_outline_agent = Agent(
    name='story_outline_agent',
    instructions='Generate a very short story ouline based on the user input.',
    model=ext_model
)


class OutlineCheckerOutput(BaseModel):
    good_quality: bool
    is_scifi: bool


outline_checker_agent = Agent(
    name='outline_checker_agent',
    instructions='Read the given story outline and judge the quality. Also determine if the outline is for a scifi story',
    model=ext_model,
    output_type=OutlineCheckerOutput
)


story_agent = Agent(
    name='sotry_agent',
    instructions='Write a short story based on the given outline.',
    model=ext_model,
    output_type=str
)

async def main():
    input_prompt = input("What kind of story do you want? ")
    outline_result = await Runner.run(
        starting_agent=story_outline_agent,
        input=input_prompt
    )

    print(f"Story outline: {outline_result.final_output}")

    # Step-2: Check the quality and genre of story outline
    outline_checker_result = await Runner.run(
        starting_agent=outline_checker_agent,
        input=outline_result.final_output
    )

    # Step-3: Add a gate to stop if the outline quality is not good or it isn't scifi
    assert isinstance(outline_checker_result.final_output, OutlineCheckerOutput), "Outline doesn't match the requirements."

    if not outline_checker_result.final_output.good_quality:
        print("Outline is not a good quality.")
        exit(0)
    
    if not outline_checker_result.final_output.is_scifi:
        print("The generated outline is not a scifi.")
        exit(0)
    
    # Step-4: Write a story on given outline
    story = await Runner.run(
        starting_agent=story_agent,
        input=outline_result.final_output
    )

    print(f"Story: {story.final_output}")


if __name__ == '__main__':
    asyncio.run(main())