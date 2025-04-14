import os
import requests
from mcp.server.fastmcp import FastMCP
import psycopg2 as pg
import logging
logging.basicConfig(level=logging.ERROR)
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("username")
host = os.getenv("host")
database = os.getenv("database")
password = os.getenv("password")

mcp = FastMCP("postgres-notion-server")

notion_base_url = "https://api.notion.com/v1/databases/{DATABASE_ID}/query"

headers = {
    "Authorization": f"Bearer {os.getenv('notion_secret')}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


@mcp.tool()
def retrieve_tickets(database_id: str):
    """
    Retrieve the all tickets from the Notion database.

    Args:
        database_id (str): The ID of the Notion database.
        
    Returns:
        dict: The query result or an error message.
    """
    url = notion_base_url.format(DATABASE_ID=database_id)
    body = {}
    try:
        response = requests.post(url, headers=headers, json=body)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@mcp.tool()
def postgres_data(query: str):
    """
    returns details of employees from the postgres database based on the user question or query

    Args:
        query: PostgresSQL query for quering the database

    Returns: 
        The query result from the database
    """
    try:
        conn = pg.connect(
            port=5432,
            host=host,
            database=database,
            password=password,
            user=username
        )
        cursor = conn.cursor()
        cursor.execute(query=query)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return str(results)

    except pg.Error as e:
        return {"error": str(e)}

