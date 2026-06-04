"""Terminal conversationnel pour la Cooking Brigade API.

Usage:
    uv run python 06-chat-cli.py
    uv run python 06-chat-cli.py --session <session_id>  # reprendre une session existante

Commandes disponibles dans le chat:
    /reset    Démarrer une nouvelle session
    /history  Afficher l'historique de la session courante
    /quit     Quitter
"""

import argparse
import sys

import httpx
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.spinner import Spinner

API_BASE = "http://localhost:8000"
TIMEOUT = 300  # secondes — le traitement par la Crew peut prendre du temps

console = Console()


def check_api() -> bool:
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def show_history(session_id: str) -> None:
    try:
        r = httpx.get(f"{API_BASE}/sessions/{session_id}/history", timeout=10)
        r.raise_for_status()
        history = r.json()["history"]
        if not history:
            console.print("[dim]Aucun historique pour cette session.[/dim]")
            return
        console.print(Rule(f"Historique — session {session_id[:8]}…"))
        for msg in history:
            if msg["role"] == "user":
                console.print(Panel(
                    msg["content"],
                    title="[bold green]Vous[/bold green]",
                    border_style="green",
                ))
            else:
                console.print(Panel(
                    Markdown(msg["content"]),
                    title="[bold blue]Brigade[/bold blue]",
                    border_style="blue",
                ))
    except Exception as e:
        console.print(f"[red]Erreur lors de la récupération de l'historique : {e}[/red]")


def send_message(session_id: str | None, message: str) -> tuple[str, str]:
    payload: dict = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    with Live(
        Spinner("dots", text="[dim]La brigade travaille…[/dim]"),
        console=console,
        refresh_per_second=10,
        transient=True,
    ):
        r = httpx.post(f"{API_BASE}/chat", json=payload, timeout=TIMEOUT)
        r.raise_for_status()

    data = r.json()
    return data["session_id"], data["response"]


def print_welcome() -> None:
    console.print(Panel.fit(
        "[bold yellow]Bienvenue à la Cooking Brigade[/bold yellow]\n\n"
        "Décrivez votre repas idéal et la brigade créera un menu sur mesure.\n"
        "[dim]Commandes : /reset · /history · /quit[/dim]",
        border_style="yellow",
        padding=(1, 4),
    ))


def main() -> None:
    parser = argparse.ArgumentParser(description="Cooking Brigade — interface terminale")
    parser.add_argument("--session", metavar="SESSION_ID", help="Reprendre une session existante")
    args = parser.parse_args()

    print_welcome()

    if not check_api():
        console.print(
            "[red bold]L'API n'est pas disponible.[/red bold]\n"
            "[dim]Démarrez-la dans un autre terminal avec :[/dim]\n"
            "  [cyan]uv run python 06-conversation.py[/cyan]"
        )
        sys.exit(1)

    session_id: str | None = args.session
    if session_id:
        console.print(f"[dim]Reprise de la session [cyan]{session_id[:8]}…[/cyan][/dim]")

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]Vous[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Au revoir ![/dim]")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            console.print("[dim]Au revoir ![/dim]")
            break

        if user_input == "/reset":
            session_id = None
            console.print("[dim]Session réinitialisée — nouvelle conversation.[/dim]")
            continue

        if user_input == "/history":
            if session_id:
                show_history(session_id)
            else:
                console.print("[dim]Aucune session en cours.[/dim]")
            continue

        try:
            session_id, response = send_message(session_id, user_input)
            console.print(f"[dim]Session : [cyan]{session_id[:8]}…[/cyan][/dim]")
            console.print(Panel(
                Markdown(response),
                title="[bold blue]Brigade[/bold blue]",
                border_style="blue",
                padding=(1, 2),
            ))
        except httpx.HTTPStatusError as e:
            console.print(f"[red]Erreur API {e.response.status_code} : {e.response.text}[/red]")
        except httpx.RequestError as e:
            console.print(f"[red]Erreur réseau : {e}[/red]")


if __name__ == "__main__":
    main()
