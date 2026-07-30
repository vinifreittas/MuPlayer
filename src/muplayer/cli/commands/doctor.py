import os
import platform
import shutil
import sys

import typer

app = typer.Typer()


@app.command("doctor")
def doctor_cmd() -> None:
    """Run system diagnostics and display environment details."""
    from rich.console import Console
    from rich.table import Table

    from muplayer.cli.utils import (
        check_engines,
        check_terminal_support,
        get_engine_version,
        get_version,
    )
    from muplayer.utils.paths import get_cache_dir, get_data_dir, get_log_dir

    console = Console()
    console.print("\n[bold cyan]=== MuPlayer System Doctor ===[/bold cyan]\n")

    # Table 1: System Info
    sys_table = Table(title="System Information", show_header=True, header_style="bold magenta")
    sys_table.add_column("Property", style="cyan")
    sys_table.add_column("Value", style="green")

    sys_table.add_row("MuPlayer Version", get_version())
    sys_table.add_row("Python Version", sys.version.split()[0])
    sys_table.add_row("OS / Platform", f"{platform.system()} {platform.release()} ({platform.machine()})")
    sys_table.add_row("Executable Path", sys.executable)
    console.print(sys_table)
    console.print()

    # Table 2: Terminal Environment
    term_table = Table(title="Terminal Environment", show_header=True, header_style="bold magenta")
    term_table.add_column("Check", style="cyan")
    term_table.add_column("Status", style="bold")
    term_table.add_column("Details", style="dim")

    is_stdin_tty = sys.stdin.isatty()
    term_table.add_row(
        "Interactive Input (stdin)",
        "[green]PASS[/green]" if is_stdin_tty else "[red]FAIL[/red]",
        "Connected to TTY" if is_stdin_tty else "Not attached to interactive TTY",
    )

    is_stdout_tty = console.is_terminal
    term_table.add_row(
        "Terminal Output (stdout)",
        "[green]PASS[/green]" if is_stdout_tty else "[red]FAIL[/red]",
        "Connected to terminal" if is_stdout_tty else "Not attached to terminal",
    )

    is_dumb = console.is_dumb_terminal
    term_table.add_row(
        "Terminal Type",
        "[red]FAIL (Dumb)[/red]" if is_dumb else "[green]PASS[/green]",
        f"TERM={os.getenv('TERM', 'not set')}",
    )

    color_sys = console.color_system
    term_table.add_row(
        "Color Support",
        "[green]PASS[/green]" if color_sys else "[red]FAIL[/red]",
        f"Detected: {color_sys}" if color_sys else "No color support detected",
    )

    cols, lines = shutil.get_terminal_size()
    term_table.add_row(
        "Terminal Dimensions",
        "[green]INFO[/green]",
        f"{cols} columns x {lines} rows",
    )

    console.print(term_table)
    console.print()

    # Table 3: Audio Engines
    eng_table = Table(title="Audio Playback Engines", show_header=True, header_style="bold magenta")
    eng_table.add_column("Engine", style="cyan")
    eng_table.add_column("Installed", style="bold")
    eng_table.add_column("Version / Path", style="dim")

    engines = check_engines()
    for engine_name in ["mpv", "vlc"]:
        path = engines[engine_name]
        if path:
            version_info = get_engine_version(engine_name) or path
            eng_table.add_row(engine_name.upper(), "[green]YES[/green]", f"{version_info} ({path})")
        else:
            eng_table.add_row(engine_name.upper(), "[red]NO[/red]", "Not found on system PATH")

    console.print(eng_table)
    console.print()

    # Table 4: Paths & Data
    path_table = Table(title="Data & Storage Paths", show_header=True, header_style="bold magenta")
    path_table.add_column("Item", style="cyan")
    path_table.add_column("Path", style="dim")

    path_table.add_row("Data Directory", str(get_data_dir()))
    path_table.add_row("Config File", str(get_data_dir() / "config.json"))
    path_table.add_row("Database File", str(get_data_dir() / "app_data.db"))
    path_table.add_row("Logs Directory", str(get_log_dir()))
    path_table.add_row("Cache Directory", str(get_cache_dir()))
    console.print(path_table)
    console.print()

    # Summary
    is_term_ok, term_err = check_terminal_support()
    has_engine = bool(engines["mpv"] or engines["vlc"])

    if is_term_ok and has_engine:
        console.print("[bold green]✓ Everything looks good! MuPlayer is ready to run.[/bold green]\n")
    else:
        console.print("[bold red]✗ System configuration issue detected:[/bold red]")
        if not has_engine:
            console.print("  - Missing audio engine ('mpv' or 'vlc'). Run: [cyan]muplayer setup[/cyan]")
        if not is_term_ok:
            console.print(f"  - Terminal issue: {term_err}")
        console.print()
