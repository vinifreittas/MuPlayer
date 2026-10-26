import json
from typing import Annotated

import typer

from muplayer.infrastructure.logging import LOG_BACKUPS
from muplayer.infrastructure.system import get_log_dir

app = typer.Typer()


def _format_log_entry(entry: dict) -> str:
    timestamp = entry.get("timestamp", "")
    level = entry.get("level", "INFO")
    name = entry.get("name", "")
    lineno = entry.get("lineno")
    location = f"[{name}:{lineno}]" if lineno is not None else f"[{name}]"
    message = entry.get("message", "")
    line = f"[{timestamp}] {level:<8} {location} {message}"
    if entry.get("exception"):
        line += f"\n{entry['exception']}"
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
    from rich.syntax import Syntax

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
        console.print(Syntax(filtered_content, "log", theme="ansi_dark", word_wrap=True))

    console.print()
