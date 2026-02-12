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
    goal="Cherche un menu qui puisse satisfaire la demande du client.",
    backstory="""Tu es un chef renommé avec 20 ans d'expérience au sein de prestigieux établissements 
        à travers le monde. Tu sais parfaitement comprendre les demandes des clients et 
        tu sais les traduire en superbes menus aux gouts délicats et raffinés et à la présentation impeccable.
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
    goal="Trouver un vin qui s'accorde avec un menu.",
    backstory="""Vous êtes un sommelier possédant une expertise de classe mondiale en matière d'accords mets-vins.
        Vous avez une connaissance approfondie des cépages, des terroirs et des millésimes. 
        Vous savez comment équilibrer l'acidité, les tanins et la douceur avec les saveurs des aliments.
        Vous utilisez UNIQUEMENT les vins présents dans la base de donnée du restaurant.
    """,
    tool=query_wines_tool,
    verbose=True,
)

# Tasks
create_menu_task = Task(
    description="""La demande du client est la suivante : {customer_query}
    En respectant sa demande, crée un menu qui le satisfasse.
    """,
    expected_output="""Une description en 3 phrases du menu qui a été créé.
    Termine en ajoutant une suggestion de vin pour accompagner ce menu.
    """,
    agent=chef,
)

find_wine_task = Task(
    description="""Trouve un vin dans la base de donnée du restaurant qui accompagne à merveille le menu.
        Aucune recherche extérieure n'est possible.
        Utilise l'outil appelé query_wines_tool.
        N'utilise que les vins issu du résultat de la requete de base de données du restaurant avec l'outil query_wines_tool.""",
    expected_output="""Une description en 1 phrase du vin trouvé et son terroir.
        La description doit comporter le nom exact du vin trouvé dans la base de donnée du restaurant.
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

customer_query = "Nous serons 3 personnes. Nous aimons la cuisine internationale et les vins blancs."
result = brigade.kickoff(inputs={"customer_query": customer_query})
