from __future__ import annotations

import asyncio
import os
import random
import uuid
import logfire
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent, 
    Runner, 
    function_tool, 
    RunContextWrapper, 
    handoff, 
    TResponseInputItem, 
    trace, 
    ItemHelpers,
    MessageOutputItem,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
    set_default_openai_api,
    set_default_openai_client
)


from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.tracing import GLOBAL_TRACE_PROVIDER

load_dotenv()

GLOBAL_TRACE_PROVIDER.shutdown()
logfire.configure()
logfire.instrument_openai_agents()

api_key = os.getenv("GEMINI_API_KEY")
base_url = os.getenv("BASE_URL")
ext_model = os.getenv("MODEL_NAME")

if not api_key or not base_url or not ext_model:
    raise ValueError("Please set GEMINI_API_KEY, BASE_URL, and MODEL in your .env file.")

ext_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
set_default_openai_client(ext_client)
set_default_openai_api('chat_completions')


# =======================================================

### Context

class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None


### Tools

@function_tool(
    name_override="faq_lookup",
    description_override="Look up frequently asked questions about airline policies.",
)
async def faq_lookup_tool(question:str) -> str:
    question = question.lower()
    if "bag" in question or "baggage" in question:
        return (
            "You are allowed to bring one bag on the plane. "
            "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
        )
    
    elif "seats" in question or "plane" in question:
                return (
            "There are 120 seats on the plane. "
            "There are 22 business class seats and 98 economy seats. "
            "Exit rows are rows 4 and 16. "
            "Rows 5-8 are Economy Plus, with extra legroom. "
        )
    elif "wifi" in question:
        return "We have free wifi on the plane, join Airline-Wifi"
    
    return "I'm sorry, I don't know the answer to that question."

@function_tool()
async def update_seat(
      
      context: RunContextWrapper[AirlineAgentContext],
      confirmation_number: str,
      new_seat: str,
) -> str:
    """
    Update the seat number for a a given confirmation number.

    Args:
        confirmation_number (str): The confirmation number of the passenger.
        new_seat (str): The new seat number to assign to the passenger.
    """
    # Update the context based on the customer's input
    context.context.confirmation_number = confirmation_number
    context.context.seat_number = new_seat

    # Ensure that the flight number is set by the incoming handoff
    assert context.context.flight_number is not None, "Flight number is required to update seat."
    return f"Updated seat to {new_seat} for confirmation number {confirmation_number} on flight {context.context.flight_number}."


### Hooks

async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
     flight_number = f"FLT-{random.randint(100, 999)}"
     context.context.flight_number = flight_number
    

### Agents

faq_agent = Agent[AirlineAgentContext](
    name="Airline FAQ Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Your are an FAQ agent. If you're speaking to a customer, you probably were transferred from triage agent.
    Use the following routine to support the customer:
    # Routine
    1. Identify the last question asked by the customer.
    2. Use the faq_lookup_tool to answer the question. Do not rely on your own knowledge.
    3. If you cannot answer the question, transfer back to the triage agent.
    """,
    tools=[faq_lookup_tool],
    handoff_description="An agent that answers frequently asked questions about airline policies.",
    model=ext_model,
)


seat_booking_agent = Agent[AirlineAgentContext](
    name="Seat Booking Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a seat booking agent. If you're speaking to a customer, you probably were transferred from triage agent.
    Use the following routine to support the customer:
    # Routine
    1. Ask for their confirmation number.
    2. Ask the customer what their desired seat number is.
    3. Use the update_seat tool to update the seat on the flight.handoff_description=
    If the customer asks question that is not related to the routine, transfer back to the triage agent.
    """,
    tools=[update_seat],
    handoff_description="A helpful agent that can update a seat on a flight.",
     model=ext_model,
)

triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a helpful triage agent. You can use your tools to delegate questions to other  appropriate agents.
    If the customer asks a question that handover to faq agent. If the customer asks a question that is related to booking a seat, handover to the seat booking agent.
    """,
    handoffs=[
         faq_agent,
         handoff(agent=seat_booking_agent, on_handoff=on_seat_booking_handoff),
    ],
    handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
    model=ext_model,
)

faq_agent.handoffs.append(triage_agent)
seat_booking_agent.handoffs.append(triage_agent)

### Run
async def main():
    current_agent: Agent[AirlineAgentContext] = triage_agent
    input_items: list[TResponseInputItem] = []
    context = AirlineAgentContext()

    conversation_id = uuid.uuid4().hex[:16]

    while True:
        user_input = input("Enter your message (or 'exit' to quit): ")
        if user_input.lower() == "exit" or user_input.lower() == "quit":
            print("Exiting...")
            break
        
        with trace("Customer Service", group_id=conversation_id):
            input_items.append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )
            result = await Runner.run(starting_agent=current_agent, input=input_items, context=context)

            for new_item in result.new_items:
                agent_name = new_item.agent.name
                if isinstance(new_item, MessageOutputItem):
                     print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
                elif isinstance(new_item, HandoffOutputItem):
                    print(f"Handed from {new_item.source_agent.name} to {new_item.target_agent.name}")
                elif isinstance(new_item, ToolCallItem):
                     print(f"{agent_name} calling tool")
                elif isinstance(new_item, ToolCallOutputItem):
                    print(f"{agent_name} tool call output: {new_item.output}")
                else:
                    print(f"{agent_name}: Skipping Item: {new_item.__class__.__name__}")
            
            # Update the current agent based on the result
            current_agent = result.last_agent
            input_items = result.to_input_list()
        

if __name__ == "__main__":
    asyncio.run(main())

 

