import json
from codecs import backslashreplace_errors

from crewai import Agent, Task, Crew

# Create an agent
chef = Agent(
    role="Chef",
    goal="Cherche un menu qui puisse satisfaire la demande du client.",
    backstory="""Tu es un chef renommé avec 20 ans d'expérience au sein de prestigieux établissements 
        à travers le monde. Tu sais parfaitement comprendre les demandes des clients et 
        tu sais les traduire en superbes menus aux gouts délicats et raffinés et à la présentation impeccable.
    """,
    verbose=True,
)

create_menu_task = Task(
    description="""La demande du client est la suivante : {customer_query}
    En respectant sa demande, crée un menu qui le satisfasse.
    """,
    expected_output="""Une description en 3 phrases du menu qui a été créé.
    Termine en ajoutant une suggestion de vin pour accompagner ce menu.
    """,
    agent=chef,
)

brigade = Crew(
    name="02 - Brigade",
    agents=[chef],
    tasks=[create_menu_task],
    verbose=True,
    tracing=True,
)

customer_query = "Nous sommes 2 personnes et nous sommes végétariens."
result = brigade.kickoff(inputs={"customer_query": customer_query})
