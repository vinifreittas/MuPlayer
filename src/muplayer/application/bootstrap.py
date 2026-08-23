import asyncio
import logging

import typer

from muplayer.application.library_service import LibraryService
from muplayer.application.playback_service import PlaybackService
from muplayer.application.search_service import SearchService
from muplayer.infrastructure.audio import PlayerAPI
from muplayer.infrastructure.cache import Cache
from muplayer.infrastructure.config import ConfigManager
from muplayer.infrastructure.database import DatabaseManager
from muplayer.infrastructure.i18n import set_locale
from muplayer.infrastructure.logging import setup_logging
from muplayer.infrastructure.search import SearchAPI
from muplayer.infrastructure.system import (
    check_engines,
    check_terminal_support,
    get_cache_dir,
    get_data_dir,
    get_log_dir,
)
from muplayer.interface.tui.app import MuPlayer

logger = logging.getLogger(__name__)


def resolve_engine(engines: dict[str, bool]) -> str:
    """Returns the available engine (preferring mpv)."""
    return "mpv" if engines.get("mpv") else "vlc"


def validate_environment() -> dict[str, bool]:
    """Executes pre-flight checks for system dependencies and terminal support."""
    engines = check_engines()
    if not engines.get("mpv") and not engines.get("vlc"):
        typer.secho(
            "\nError: Neither 'mpv' nor 'vlc' library was found on your system.\n"
            "MuPlayer needs one of these engines to play music.\n\n"
            "Please run: muplayer setup",
            fg="red",
            bold=True,
            err=True,
        )
        raise typer.Exit(code=1)

    is_terminal_ok, terminal_error = check_terminal_support()
    if not is_terminal_ok:
        typer.secho(
            f"\nError: Terminal environment is not supported for Textual TUI.\n"
            f"Reason: {terminal_error}\n\n"
            "Please run MuPlayer inside a modern interactive terminal emulator.",
            fg="red",
            bold=True,
            err=True,
        )
        raise typer.Exit(code=1)

    return engines


def run_app(debug: bool = False, force: bool = False) -> None:
    """Composition Root: Bootstraps services, runs TUI app, and cleans up resources."""
    log_level = logging.DEBUG if debug else logging.INFO
    data_dir = get_data_dir()
    setup_logging(log_dir=get_log_dir(), log_level=log_level)

    engines = validate_environment() if not force else check_engines()
    player_engine = resolve_engine(engines)

    config_manager = ConfigManager(config_path=data_dir / "config.json")
    set_locale(config_manager.config.language)

    # Pre-declare resource handles for safe cleanup in finally
    player_api: PlayerAPI | None = None
    search_api: SearchAPI | None = None
    db: DatabaseManager | None = None
    cache: Cache | None = None

    try:
        cache = Cache(cache_dir=get_cache_dir())
        db = DatabaseManager(db_path=data_dir / "app_data.db")
        player_api = PlayerAPI(engine=player_engine)
        search_api = SearchAPI()

        search_service = SearchService(search_api=search_api, cache=cache)
        library_service = LibraryService(db=db)
        playback_service = PlaybackService(player_api=player_api, search_api=search_api, cache=cache)

        player = MuPlayer(
            playback_service=playback_service,
            library_service=library_service,
            search_service=search_service,
            config_manager=config_manager,
        )
        player.run()
    except KeyboardInterrupt:
        typer.secho("\nMuPlayer session terminated by user.", fg="yellow")
        raise typer.Exit(code=0) from None
    except Exception as e:
        typer.secho(f"\nFatal error starting MuPlayer: {e}", fg="red", err=True)
        raise typer.Exit(code=1) from None
    finally:
        if player_api:
            player_api.close()
        if search_api:
            search_api.close()
        if db:
            asyncio.run(db.disconnect())
        if cache:
            cache.close()
