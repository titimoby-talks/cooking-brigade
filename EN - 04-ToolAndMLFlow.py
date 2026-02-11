import json
from codecs import backslashreplace_errors

from crewai import Agent, Task, Crew
from crewai.tools import tool

from database.RestaurantDB import RestaurantDB

import mlflow

mlflow.crewai.autolog()

# Optional: Set a tracking URI and an experiment name if you have a tracking server
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("Brigade")

# Agents
chef = Agent(
    role="Chef",
    goal="Find a menu that can satisfy the customer's request.",
    backstory="""You are a renowned chef with 20 years of experience in prestigious establishments 
        around the world. You have a perfect understanding of customer requests and 
        know how to translate them into superb menus with delicate, refined flavours and impeccable presentation.
    """,
    verbose=True,
)

@tool
def query_wines_tool():
    """Query the wines table from the RestaurantDB."""
    db = RestaurantDB()
    records = db.query_wines()
    return [record.string_representation() for record in records]

sommelier = Agent(
    role="Sommelier",
    goal="Finding a wine that pairs well with a menu.",
    backstory="""You are a sommelier with world-class expertise in food and wine pairings.
        You have in-depth knowledge of grape varieties, terroirs and vintages.
        You know how to balance acidity, tannins and sweetness with food flavours.
        You ONLY use wines listed in the restaurant's database.
    """,
    tool=query_wines_tool,
    verbose=True,
)

# Tasks
create_menu_task = Task(
    description="""The customer's request is as follows: {customer_query}
        In accordance with their request, create a menu that satisfies them.
    """,
    expected_output="""A three-sentence description of the menu that has been created.
        Finish by adding a wine suggestion to accompany this menu.
    """,
    agent=chef,
)

find_wine_task = Task(
    description="""Find a wine in the restaurant's database that pairs perfectly with the menu.
        No external searches are possible.
        Use the tool called query_wines_tool to access the wines in the restaurant's database.
        Only use wines from the results of the restaurant's database query using the query_wines_tool tool.
    """,
    expected_output="""A one-sentence description of the wine found and its terroir.
        The description must include the exact name of the wine found in the restaurant's database.
    """,
    agent=sommelier,
    context=[create_menu_task],
)

# Crew and execution
brigade = Crew(
    name="03 - Brigade",
    agents=[chef, sommelier],
    tasks=[create_menu_task, find_wine_task],
    verbose=True,
    tracing=True,
)

customer_query = "There will be three of us. We enjoy international cuisine and white wines."
result = brigade.kickoff(inputs={"customer_query": customer_query})
