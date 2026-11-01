import json
from typing import Annotated

import typer
from rich.markup import escape

from muplayer.infrastructure.logging import LOG_BACKUPS
from muplayer.infrastructure.system import get_log_dir

app = typer.Typer()

LEVEL_COLORS = {
    "DEBUG": "dim",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "bold red",
    "CRITICAL": "bold white on red",
}


def _format_log_entry(entry: dict) -> str:
    timestamp = entry.get("timestamp", "")
    level = entry.get("level", "INFO")
    raw_name = entry.get("name", "")
    name = raw_name.removeprefix("muplayer.infrastructure.").removeprefix("muplayer.")
    lineno = entry.get("lineno")
    location = f"{name}:{lineno}" if lineno is not None else name
    message = escape(str(entry.get("message", "")))

    color = LEVEL_COLORS.get(level, "white")
    line = f"[dim]{timestamp}[/dim] [{color}][{level}][/{color}] [cyan]{location}[/cyan]: {message}"
    exc = entry.get("exception")
    if exc:
        line += f"\n[dim red]{escape(str(exc))}[/dim red]"
    return line


def _filter_log_content(content: str, include_debug: bool) -> str:
    """Parse structured JSONL logs and filter out DEBUG entries unless include_debug is True."""
    filtered_lines: list[str] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            if not include_debug and " DEBUG " in raw_line:
                continue
            filtered_lines.append(raw_line)
            continue

        if not isinstance(entry, dict):
            continue

        if not include_debug and entry.get("level") == "DEBUG":
            continue

        filtered_lines.append(_format_log_entry(entry))

    return "\n".join(filtered_lines)


@app.command("log")
def log_cmd(
    index: Annotated[
        int | None,
        typer.Argument(
            help=(f"Log file to display (1 = most recent, up to {LOG_BACKUPS}). Defaults to the most recent log."),
            show_default=False,
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            "-d",
            help="Include DEBUG level entries in the output.",
        ),
    ] = False,
) -> None:
    """Display a saved MuPlayer log file."""
    from rich.console import Console
    from rich.rule import Rule

    console = Console()
    log_dir = get_log_dir()
    log_files = sorted(log_dir.glob("app-*.log"), key=lambda f: f.stat().st_mtime, reverse=True)

    if not log_files:
        console.print("[yellow]No log files found.[/yellow]")
        raise typer.Exit(1)

    available = log_files[:LOG_BACKUPS]

    if index is None:
        target = available[0]
        label = "most recent"
    else:
        if not (1 <= index <= LOG_BACKUPS):
            console.print(f"[red]Invalid index {index}. Must be between 1 and {LOG_BACKUPS}.[/red]")
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
    filtered_content = _filter_log_content(content, include_debug=debug)
    if not filtered_content.strip():
        console.print("[dim]Log file is empty.[/dim]")
    else:
        console.print(filtered_content, highlight=False, soft_wrap=True)

    console.print()
