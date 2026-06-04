from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, Memory
import uuid
from typing import Optional

app = FastAPI(title="Cooking Brigade API", version="1.0.0")

memory = Memory()
memory.reset()
print(memory.tree())

# session_id -> liste de {"role": "user"|"assistant", "content": str}
sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    history: list[dict]


def format_history_for_crew(history: list[dict]) -> str:
    if not history:
        return ""
    lines = ["=== Historique de la conversation ==="]
    for msg in history:
        label = "Client" if msg["role"] == "user" else "Brigade"
        lines.append(f"{label}: {msg['content']}")
    lines.append("=== Fin de l'historique ===")
    return "\n".join(lines)


def build_crew() -> Crew:
    chef_agent = Agent(
        role="ChefAgent",
        goal="Analyze customer's requests and create structured menus with ingredient quantities",
        backstory=(
            "You are a renowned Chef with 20 years of experience in fine dining "
            "restaurants across France. You excel at understanding client requirements and "
            "translating them into exquisite menus that balance flavors, textures, and "
            "presentation. You specialize in French and Italian cuisine but can adapt to "
            "any culinary style. You work closely with your Sommelier for perfect wine. "
            "You always create menus with three courses: entrée (starter), plat (main course), and dessert. "
            "When the conversation history mentions a previous menu, take it into account to propose variations or improvements."
        ),
        allow_delegation=False,
        max_iterations=2,
        max_retry=1,
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
        max_iterations=2,
        max_retry=1,
    )

    report_agent = Agent(
        role="ReportAgent",
        goal="Creating comprehensive, well-structured reports based on the work of your coworkers.",
        backstory="""Creating comprehensive, well-structured reports based on research findings.
        Your role is to synthesize information and present it in a clear, professional format.
        """,
        allow_delegation=False,
        max_iterations=1,
        max_retry=1,
    )

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

        Follow these steps exactly once, in order. Do NOT repeat any step.

        STEP 1 — Activate ChefAgent:
            - Delegate the menu creation to ChefAgent
            - Wait for ChefAgent to return the menu, then proceed to STEP 2

        STEP 2 — Activate SommelierAgent:
            - Delegate wine pairing to SommelierAgent, providing the menu from STEP 1
            - If SommelierAgent responds with "I find a wine": proceed directly to STEP 4
            - If SommelierAgent responds with "I don't find a wine": proceed to STEP 3
            - You may only loop back to ChefAgent ONCE. After that, go to STEP 4 regardless.

        STEP 3 — Activate ChefAgent (revision, one time only):
            - Delegate a menu revision to ChefAgent
            - Then activate SommelierAgent one final time
            - Regardless of the result, proceed to STEP 4

        STEP 4 — Activate ReportAgent (FINAL STEP):
            - Delegate the final report to ReportAgent
            - Once ReportAgent returns its report, the workflow is COMPLETE
            - Do NOT activate any further agents
            - Return the ReportAgent's output as your final answer
        """,
        allow_delegation=True,
        max_iterations=10,
        max_retry=1,
    )

    menu_creation_task = Task(
        description="""Analyze the following customer request and create a menu.

{customer_query}
        """,
        expected_output="A concise and clear description of the menu with three courses: entrée (starter), plat (main course), and dessert.",
        agent=chef_agent,
        async_execution=False,
    )

    sommelier_task = Task(
        description="""Search a wine that pairs perfectly with the menu.""",
        expected_output="The name and description of the wine you found",
        agent=sommelier_agent,
        context=[menu_creation_task],
    )

    report_task = Task(
        description="""Produce a final report based on the menu and the wine found.""",
        expected_output="A nice and polished text describing the menu.",
        agent=report_agent,
        async_execution=False,
        context=[menu_creation_task, sommelier_task],
    )

    crew = Crew(
        agents=[chef_agent, sommelier_agent, report_agent],
        tasks=[menu_creation_task, sommelier_task, report_task],
        memory=memory,
        manager_agent=waiter_agent,
        process=Process.hierarchical,
        verbose=True,
        tracing=True,
    )

    return crew


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = []

    history = sessions[session_id]
    history_context = format_history_for_crew(history)

    if history_context:
        full_query = f"{history_context}\n\nNouvelle demande du client: {request.message}"
    else:
        full_query = request.message

    crew = build_crew()
    try:
        result = await run_in_threadpool(
            lambda: crew.kickoff(inputs={"customer_query": full_query})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": result.raw})

    return ChatResponse(
        session_id=session_id,
        response=result.raw,
        history=history,
    )


@app.get("/sessions/{session_id}/history")
async def get_history(session_id: str) -> dict:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"session_id": session_id, "history": sessions[session_id]}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable")
    del sessions[session_id]
    return {"message": f"Session {session_id} supprimée"}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "sessions_actives": len(sessions)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
