import os
import asyncio
import google
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm 
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import logging
logging.basicConfig(level=logging.ERROR)
from dotenv import load_dotenv
from tools import postgres_data, retrieve_tickets

load_dotenv()

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
postgres_agent = Agent(
    name="postgres_agent",
    model=LiteLlm('mistral/mistral-large-latest'),
    description="Executes queries on postgres database and retrieves data",
    instruction="You are a helpful assistant specialized in interacting with a PostgreSQL database. "
                "Your primary goal is to execute SQL queries and retrieve relevant data. "
                "When the user provides a query or asks for data, "
                "you MUST use the appropriate database tools to access the PostgreSQL database. "
                "Analyze the tool's response: if the status is 'error', inform the user politely about the error message. "
                "If the status is 'success', present the retrieved data clearly and concisely to the user. "
                "Only use the tool when the user provides a valid data request.",
    tools=[postgres_data],
)

notion_agent = Agent(
    name="notion_agent",
    model=LiteLlm('mistral/mistral-large-latest'),
    description="Retrieves tickets from a Notion database using a given database ID.",
    instruction=(
        "You are a helpful assistant specialized in retrieving ticket information from a Notion database. "
        "The user will provide a Notion database ID, and your task is to use the appropriate tool to fetch the ticket data. "
        "You MUST use the tool to query the Notion database using the provided ID. "
        "After receiving the tool's response: "
        "- If the status is 'error', inform the user politely about the error message. "
        "- If the status is 'success', present the retrieved ticket data clearly and concisely. "
        "Only use the tool when the user provides a valid database ID."
    ),
    tools=[retrieve_tickets],  
)

root_agent = Agent(
    name="manager_agent",
    model=LiteLlm('mistral/mistral-large-latest'),
    description="A high-level manager agent that delegates tasks to specialized agents for PostgreSQL and Notion.",
    instruction=(
        "You are a smart and helpful manager agent that delegates user requests to specialized agents. "
        "You have access to two agents: one that handles PostgreSQL queries (`postgres_agent`) "
        "and one that retrieves ticket data from Notion (`notion_agent`). "
        "\n\n"
        "When a user asks for database-related information or wants to run a SQL query, delegate the task to `postgres_agent`. "
        "When the user asks for ticket information from a Notion database and provides a Notion database ID, delegate the task to `notion_agent`."
        "\n\n"
        "Always choose the most appropriate agent based on the user's intent. Wait for the selected agent’s response and then present it back to the user in a clear and friendly manner. "
        "If the input is unclear or invalid, politely ask the user for clarification."
    ),
    sub_agents=[postgres_agent, notion_agent]
)

session_service = InMemorySessionService()

APP_NAME = "agent_team"
USER_ID = "user_1_agent_team"
SESSION_ID = "session_001_agent_team"

session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

actual_root_agent =root_agent

runner_agent_team = Runner(
    agent=actual_root_agent, 
    app_name=APP_NAME,       
    session_service=session_service
)

async def call_agent_async(query: str):
  """Sends a query to the agent and prints the final response."""
  print(f"\n>>> User Query: {query}")

  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "Agent did not produce a final response."

  async for event in runner_agent_team.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
      
      if event.is_final_response():
          if event.content and event.content.parts:
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate:
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          break 

  print(f"<<< Agent Response: {final_response_text}")

async def run_conversation():
    await call_agent_async(input('Enter the query : '))
if __name__ == "__main__":
    asyncio.run(run_conversation())
       