from __future__ import annotations

from typing import Annotated

import typer

from muplayer.infrastructure.system import get_log_dir

MAX_LOGS = 5

app = typer.Typer()


@app.command("log")
def log_cmd(
    index: Annotated[
        int | None,
        typer.Argument(
            help=(f"Log file to display (1 = most recent, up to {MAX_LOGS}). Defaults to the most recent log."),
            show_default=False,
        ),
    ] = None,
) -> None:
    """Display a saved MuPlayer log file."""
    from rich.console import Console
    from rich.rule import Rule
    from rich.syntax import Syntax

    console = Console()
    log_dir = get_log_dir()
    log_files = sorted(log_dir.glob("app-*.log"), key=lambda f: f.stat().st_mtime, reverse=True)

    if not log_files:
        console.print("[yellow]No log files found.[/yellow]")
        raise typer.Exit(1)

    available = log_files[:MAX_LOGS]

    if index is None:
        target = available[0]
        label = "most recent"
    else:
        if not (1 <= index <= MAX_LOGS):
            console.print(f"[red]Invalid index {index}. Must be between 1 and {MAX_LOGS}.[/red]")
            raise typer.Exit(1)
        if index > len(available):
            console.print(f"[yellow]Log #{index} does not exist. Only {len(available)} log(s) available.[/yellow]")
            raise typer.Exit(1)
        target = available[index - 1]
        label = f"#{index}"

    console.print()
    console.print(
        Rule(
            f"[bold cyan]MuPlayer Log {label}[/bold cyan]  [dim]{target.name}[/dim]",
            style="cyan",
        )
    )

    if len(available) > 1:
        console.print(
            "[dim]Tip: use [cyan]muplayer log <n>[/cyan] to view older logs "
            f"(1 = newest, {len(available)} available).[/dim]"
        )

    console.print()

    content = target.read_text(encoding="utf-8", errors="replace")
    if not content.strip():
        console.print("[dim]Log file is empty.[/dim]")
    else:
        console.print(Syntax(content, "log", theme="ansi_dark", word_wrap=True))

    console.print()
