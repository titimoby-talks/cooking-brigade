from crewai import Crew, Process, Agent, Task, CrewOutput
from crewai.project import crew, agent, task, CrewBase
from crewai.types.streaming import CrewStreamingOutput

@CrewBase
class CookingCrew:
    """Orchestrates the multi-agent workflow using CrewAI.

    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def chef_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["chef_agent"],
            verbose=True,
            allow_delegation=True,
        )

    @task
    def chef_task(self) -> Task:
        return Task(
            config=self.tasks_config["chef_task"]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically collected by the @agent decorator
            tasks=self.tasks,    # Automatically collected by the @task decorator.
            process=Process.sequential,
            verbose=True,
        )

    def execute(self, user_query: str) -> CrewOutput | CrewStreamingOutput:
        return self.crew().kickoff(inputs={"user_query": user_query})