### Agents
from crewai import Agent, Task, Crew, Process
from rich.progress import TaskID

chef_agent = Agent(
    role="ChefAgent",
    goal="Analyze customer's requests and create structured menus with ingredient quantities",
    backstory=(
        "You are a renowned Chef with 20 years of experience in fine dining "
        "restaurants across France. You excel at understanding client requirements and "
        "translating them into exquisite menus that balance flavors, textures, and "
        "presentation. You specialize in French and Italian cuisine but can adapt to "
        "any culinary style. You work closely with your Sommelier for perfect wine. "
        "You always create "
        "menus with three courses: entrée (starter), plat (main course), and dessert."
    ),
    allow_delegation=False,
    max_iterations=3,
    max_retry=2,
)

sommelier_agent = Agent(
    role="SommelierAgent",
    goal="Select wines that pair perfectly with menus and justify choices",
    backstory="""
                You are a Sommelier with world-class expertise in French and Italian 
                wine pairing. You have extensive knowledge of grape varieties, terroirs, and 
                vintages. You know how to balance acidity, tannins, and sweetness with food 
                flavors. 
                If you don't find a wine, say "I don't find a wine"
                If you find a wine, say "I find a wine" and then describe the wine with sensory details.
                """,
    allow_delegation=False,
    max_iterations=3,
    max_retry=2,
)

report_agent = Agent(
    role="ReportAgent",
    goal="You are the ReportAgent, creating comprehensive, well-structured reports based on the wotk of your coworkers.",
    backstory="""Creating comprehensive, well-structured reports based on research findings. Your role is to synthesize information and present it in a clear, professional format.
    """,
    allow_delegation=False,
    max_iterations=3,
    max_retry=2,
)

## Supervisor Agent

waiter_agent = Agent(
    role="WaiterAgent",
    goal="""Managing and orchestrating a team of specialized AI agents. 
         Your ONLY role is to manage the workflow by activating the appropriate agent at the appropriate time.
         You are NOT responsible for evaluating the quality or content of any agent's work.
         """,
    backstory="""You are the HeadWaiter, an AI coordinator responsible for orchestrating a team of specialized AI agents. 
        Your ONLY role is to manage the workflow by activating the appropriate agent at the appropriate time. 
        You are NOT responsible for evaluating the quality or content of any agent's work.
    
    ## WORKFLOW COORDINATION RESPONSIBILITIES

    1.  **Start with Chef as coworker**:
        - Always begin the workflow by activating the ChefAgent
        - The ChefAgent will create a menu based on the customer's request
        - After the ChefAgent creates its menu, activate the SommelierAgent
        
    2.  **Activate SommelierAgent as coworker**:
        - After the ChefAgent has finished, activate the SommelierAgent
        - Provide the SommelierAgent with the menu created by the ChefAgent
        - The SommelierAgent will search a wine that pair perfectly with the menu
        - Based on the SommelierAgent search:
          * If the SommelierAgent does not find a wine, activate the ChefAgent again
          * If the SommelierAgent finds a wine, activate the ReportAgent
    
    3.  **Activate ReportAgent as coworker**:
        - After the SommelierAgent has found a wine
        - The ReportAgent will create the final report based on the menu and the wine found
        - This is the final step, do NOT activate any other agent
        - IMPORTANT: Once the ReportAgent submits its report, the workflow is COMPLETE
        - Do NOT activate any other agents after the ReportAgent has submitted its report
        - The entire process ends when the ReportAgent delivers its final report    
    """,
    allow_delegation=True,
    max_iterations=1,
    max_retry=2,
    #    verbose=True,
)

menu_creation_task = Task(
    description="""Analyze {customer_query} and create menu
    """,
    expected_output="A concise and clear description of the menu with three courses: entrée (starter), plat (main course), and dessert.",
    agent=chef_agent,
    async_execution=False,
)

sommelier_task = Task(
    description="""Search a wine that pair perfectly with the menu.""",
    expected_output="The name and description of the wine you found",
    agent=sommelier_agent,
    context=[menu_creation_task],
)

menu_revision_task = Task(
    description="""Revision of the menu that does not meet the criteria of the SommelierAgent.
    Analyze {customer_query} and create menu and try to propose courses very different from the first ones.""",
    expected_output="A concise and clear description of the menu with three courses: entrée (starter), plat (main course), and dessert.",
    agent=chef_agent,
    async_execution=False,
    context=[menu_creation_task, sommelier_task],
)

report_task = Task(
    description="""Produce a final report based on the menu and the wine found.""",
    expected_output="A nice and polished text describing the menu.",
    agent=report_agent,
    async_execution=False,
    context=[menu_creation_task, sommelier_task, menu_revision_task],
    output_file="menu.txt",
)

crew = Crew(
    agents=[chef_agent, sommelier_agent, report_agent],
    tasks=[menu_creation_task, sommelier_task, menu_revision_task, report_task],
    memory=True,
    manager_agent=waiter_agent,
    process=Process.hierarchical,
    verbose=True,
    tracing=True,
)

example_query = "Menu italien pour 4 personnes, budget 150€, occasion anniversaire"
result = crew.kickoff(inputs={"customer_query": example_query})
print(result.raw)
