import asyncio
import logging

import typer

from muplayer.interface.cli.commands import register_commands

cli = typer.Typer(
    name="muplayer",
    help="MuPlayer - A lightweight music app for terminal.",
    add_completion=False,
)
register_commands(cli)


def _fail(msg: str) -> None:
    """Print an error message and exit the application."""
    typer.secho(f"\nError: {msg}", fg="red", bold=True, err=True)
    raise typer.Exit(code=1)


def _validate_environment(force: bool, engines: dict, check_terminal, detect_js) -> None:
    """Run pre-flight checks unless force mode is enabled."""
    if force:
        return

    if not (engines.get("mpv") or engines.get("vlc")):
        _fail(
            "Neither 'mpv' nor 'vlc' library was found on your system.\n"
            "MuPlayer needs one of these engines to play music.\n\n"
            "Please run: muplayer setup"
        )

    is_terminal_ok, terminal_error = check_terminal()
    if not is_terminal_ok:
        _fail(
            f"Terminal environment is not supported for Textual TUI.\n"
            f"Reason: {terminal_error}\n\n"
            "Please run MuPlayer inside a modern interactive terminal emulator."
        )

    if not detect_js():
        _fail(
            "No JavaScript runtime (quickjs, node, deno, or bun) found on system PATH.\n"
            "Required to extract YouTube audio stream URLs via yt-dlp.\n\n"
            "Please install QuickJS or Node.js on your system."
        )


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", "-f", help="Force start, bypassing checks."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging mode."),
) -> None:
    """Main application launcher."""
    if ctx.invoked_subcommand is not None:
        return

    # Lazy-load dependencies to keep '--help' and CLI subcommands fast
    import diskcache

    from muplayer.application.config_service import ConfigService
    from muplayer.application.library_service import LibraryService
    from muplayer.application.playback_service import PlaybackService
    from muplayer.application.search_service import SearchService
    from muplayer.infrastructure.audio import AudioPlayerAdapter
    from muplayer.infrastructure.config_manager import ConfigManager
    from muplayer.infrastructure.database import TortoiseStorageAdapter
    from muplayer.infrastructure.i18n import set_locale
    from muplayer.infrastructure.logging import setup_logging
    from muplayer.infrastructure.system import (
        check_engines,
        check_terminal_support,
        detect_js_runtime,
        get_cache_dir,
        get_data_dir,
        get_default_browser,
        get_log_dir,
    )
    from muplayer.infrastructure.youtube import YouTubeMediaProvider
    from muplayer.interface.tui.app import MuPlayer

    # 1. Logging & Environment Validation
    setup_logging(log_dir=get_log_dir(), log_level=logging.DEBUG if debug else logging.INFO)
    engines = check_engines()
    _validate_environment(force, engines, check_terminal_support, detect_js_runtime)

    # 2. Setup Configuration
    data_dir = get_data_dir()
    config_manager = ConfigManager(config_path=data_dir / "config.json")
    config_service = ConfigService(config_port=config_manager)
    set_locale(config_service.config.language)

    # 3. Bootstrapping & Resource Management
    audio_player = youtube_provider = storage = cache = None

    try:
        cache = diskcache.Cache(str(get_cache_dir()))
        storage = TortoiseStorageAdapter(db_path=data_dir / "app_data.db")
        player_engine = "mpv" if engines.get("mpv") else "vlc"
        audio_player = AudioPlayerAdapter(engine=player_engine)
        youtube_provider = YouTubeMediaProvider(js_runtime=detect_js_runtime(), browser=get_default_browser())

        app = MuPlayer(
            playback_service=PlaybackService(audio_player, youtube_provider, cache),
            library_service=LibraryService(storage),
            search_service=SearchService(youtube_provider, cache),
            config_service=config_service,
        )
        app.run()

    except KeyboardInterrupt:
        typer.secho("\nMuPlayer session terminated by user.", fg="yellow")
        raise typer.Exit(code=0) from None
    except Exception as e:
        _fail(f"Fatal error starting MuPlayer: {e}")
    finally:
        if audio_player:
            audio_player.close()
        if youtube_provider:
            youtube_provider.close()
        if storage:
            asyncio.run(storage.disconnect())
        if cache:
            cache.close()


if __name__ == "__main__":
    cli()
