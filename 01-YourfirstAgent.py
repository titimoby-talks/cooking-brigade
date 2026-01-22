from crewai import Agent

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

# Use kickoff() to interact directly with the agent
result = chef.kickoff("Nous sommes 3 personnes et nous aimons la cuisine coréenne.")

# Access the raw response
print(result.raw)
