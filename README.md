# Cooking Brigade

Demo projects of a multi-agents system modeled after a professional kitchen brigade.

1. [Your first Agent](01-YourfirstAgent.py)
2. [Your first Crew](02-YourfirstCrew.py)
3. A demo with [multiple Agents in a Crew](03-MultiAgentsCrew.py) 
4. A demo with a [Tool and Observability with MLFlow](04-ToolAndMLFlow.py)
5. A [supervisor scenario](05-SupervisorAgent.py) where an agent manages 3 other agents

Before running any demo, create an environment variable OPENAI_API_KEY with a valid OpenAI key.
You can then launch the demos with:

``` bash
uv sync
uv run XXX.py
```

`uv` is a wondefrul tool to manage your Python projects.  
Refer to the [documentation](https://docs.astral.sh/uv/) ton install and discover how it will improve your developer's life 💞