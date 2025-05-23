import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,
    ItemHelpers,
    MessageOutputItem,


)

"""
This example shows the agents-as-tools pattern. The frontline agent receives a user message and
then picks which agents to call, as tools. In this case, it picks from a set of translation
agents.
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
spanish_agent = Agent(
    name="spanish_agent",
    instructions="You translate the user's message to Spanish",
    handoff_description="An english to spanish translator",
    model=ext_model
)


french_agent = Agent(
    name="french_agent",
    instructions="You translate the user's message to French",
    handoff_description="An english to french translator",
    model=ext_model
)

italian_agent = Agent(
    name="italian_agent",
    instructions="You translate the user's message to Italian",
    handoff_description="An english to italian translator",
    model=ext_model
)

orchestrator_agent = Agent(
    name='orchestrator_agent',
    instructions=(
        "You are a translation agent. You use the tools given to you to translalte"
        "If asked for multiple translation, you call the relevant tools in order."
        "You never translate on your own. You always use the provided tools to translate."

    ),
    tools=[
        spanish_agent.as_tool(
            tool_name='translate_to_spanish',
            tool_description='translate the user message to spanish language'
        ),
        french_agent.as_tool(
            tool_name='translate_to_french',
            tool_description='Translate the user\'s message to french language.'
        ),
        italian_agent.as_tool(
            tool_name='translate_to_italian',
            tool_description="Translate the user's message to italian language."
        )
    ],
    model=ext_model
)

synthesizer_agent = Agent(
    name='synthesizer_agent',
    instructions=(
        "You are a synthesizer agent. You inspect the translations, correct if needed."
    ),
    model=ext_model
)

async def main():
    input_prompt = input("What would you like to be translated? ")
    orchestrator_result = await Runner.run(
        starting_agent=orchestrator_agent,
        input=input_prompt
    )

    # print(f"Orchestrator Result: ", orchestrator_result)
    # print("===========================================")
    # print(f"Raw Response: {orchestrator_result.raw_responses}")
    # print("===========================================")
    # print(f"Context Wrapper: {orchestrator_result.context_wrapper}")
    # print("===========================================")
    # print(f"Input: {orchestrator_result.input}")
    # print("===========================================")
    # print(f"Last Agent: {orchestrator_result.last_agent}")
    # print("===========================================")
    # print(f"Input Guardrail Result: {orchestrator_result.input_guardrail_results}")
    # print("===========================================")
    # print(f"Output Guardrail Result: {orchestrator_result.output_guardrail_results}")
    # print("===========================================")
    # print(f"Input Guardrail Result: {orchestrator_result.input_guardrail_results}")
    # print("===========================================")
    # print(f"Last Response Id: {orchestrator_result.last_response_id}")
    # print("===========================================")
    # print(f"_last_agent: {orchestrator_result._last_agent}")
    # print("===========================================")
    # print(f"New Items: {orchestrator_result.new_items}")
    # print("===========================================")
    # print(f"Test to Input List: {orchestrator_result.to_input_list()}")
    # print("===========================================")

    for item in orchestrator_result.new_items:
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            if text:
                print("===========================================")
                print(f"- Translate Step: {text}")
                print("===========================================")
    
    # synthesizer_result = await Runner.run(
    #     starting_agent=synthesizer_agent,
    #     input=orchestrator_result.to_input_list()
    # )

    # print(f"Synthesizer Result: {synthesizer_result}")

    # print(f"Final Response: {synthesizer_result.final_output}")


if __name__ == '__main__':
    asyncio.run(main())