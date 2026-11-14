# 🤖 AGENTS.md — Developer & Agent Guidelines for MuPlayer

This document provides architectural context, repository navigation, core contracts, and development commands to quickly situate developers and AI agents working on the **MuPlayer** repository.

---

## 📌 1. Project Overview & Product Vision

**MuPlayer** is a lightweight, efficient terminal-based audio player (TUI) streaming YouTube audio. It is designed specifically for developers and terminal power users who want a clean, fast, distraction-free listening experience without keeping a web browser open.

### Core Product Scope & Principles
* **Primary Scope:** Pure YouTube streaming via `yt-dlp` (search, stream URL extraction, public playlist URL import).
* **CLI vs TUI Boundary:** The CLI (Typer) is strictly for diagnostics, setup, and package maintenance (`setup`, `doctor`, `log`, `update`, `version`). The listening, queueing, and media playback UX is 100% contained inside the Textual TUI.
* **Local Library Scope:** SQLite persistence (Tortoise ORM) for user custom playlists, saved/favorite tracks, and play history.
* **Caching & Memory Policy:** Fast disk cache (`~/.cache/MuPlayer/`) for search queries (5 min TTL) and stream URLs (1h TTL). Audio is streamed in-memory via MPV/VLC without downloading local audio files.

### Tech Stack
* **Language:** Python >= 3.12 (managed via `uv`)
* **TUI Interface:** [Textual](https://textualize.io) (CSS-styled, reactive widgets, views, modals, built-in themes)
* **CLI Framework:** [Typer](https://typer.tiangolo.com) + [Rich](https://rich.readthedocs.io)
* **Audio Engine:** `mpv` (`python-mpv`) with fallback to `vlc` (`python-vlc`)
* **Streaming & Search:** `yt-dlp` (requires system JavaScript runtime: `quickjs`, `node`, `deno`, or `bun`) + browser cookie detection via `installed-browsers`
* **Database & Cache:** `SQLite` via `Tortoise ORM` & `Aerich` migrations | `diskcache` for response caching
* **Tooling:** `ruff` (linter/formatter), `pytest` / `pytest-asyncio` / `pytest-cov` (testing), `deadcode`

### Standard XDG Directory Structure (`platformdirs`)
* **Data (DB, Config, Binaries, Libs):** `~/.local/share/MuPlayer/` (`app_data.db`, `config.json`, `bin/`, `libs/`)
* **Cache:** `~/.cache/MuPlayer/`
* **Logs:** `~/.local/state/MuPlayer/logs/` (`muplayer.log`)

---

## 🏗️ 2. Clean Architecture & System Data Flow

MuPlayer strictly follows **Layered Clean Architecture**:

```
src/muplayer/
├── domain/           # Pure entities (Song, Playlist, AppConfig) & state (QueueState). No external dependencies.
├── application/      # Use case orchestrators (Playback, Search, Library, Config), Ports & Composition Root.
├── infrastructure/   # Adapters (Audio, Search, Database, System, Cache, Config, i18n, Logging).
└── interface/        # Presentation layer: CLI commands and Textual TUI (App, mixins, views, modals, widgets).
```

### ⚠️ The Golden Dependency Rule
```
domain  ←  application  ←  infrastructure
                         ←  interface
```

* **Domain (`domain/`)**: Pure core models & state. CANNOT import from any other layer.
* **Application (`application/`)**: Orchestrates use cases & defines abstract ports. Imports ONLY from `domain`.
* **Infrastructure (`infrastructure/`)**: Concrete engine adapters. Imports from `domain` and `application`.
* **Interface (`interface/`)**: Presentation layer (TUI/CLI). Imports from `domain`, `application`, and `infrastructure` (via composition root).

### Data & Execution Flow Pattern
`User Input (TUI / CLI)` ➔ `Controller Mixin / Command` ➔ `Application Service` ➔ `Infrastructure Port` ➔ `Adapter Engine (MPV/VLC, yt-dlp, Tortoise)` ➔ `Reactive State` ➔ `Textual UI View`

---

## 🗺️ 3. Repository Directory Map

```
src/muplayer/
├── main.py                          # Composition Root: Typer CLI, pre-flight checks, DI & TUI launcher
├── domain/                          # Pure business entities (no external dependencies)
│   ├── config.py                    # AppConfig Pydantic model (language, theme, volume, search_limit)
│   ├── models.py                    # Song, Playlist Pydantic models with validation
│   └── state.py                     # QueueState (tracks, index, active song, shuffle, repeat)
├── application/                     # Application orchestrators & use cases
│   ├── config_service.py            # Configuration & user preferences service
│   ├── library_service.py           # Playlists, favorites, and play history service
│   ├── playback_service.py          # Playback & queue control logic with URL cache
│   ├── search_service.py            # Search orchestration service with query cache
│   └── ports/                       # Abstract protocols (AudioPort, ConfigPort, MediaPort, SearchPort, StoragePort)
├── infrastructure/                  # Infrastructure adapters
│   ├── audio/                       # Audio engine adapter
│   │   ├── backends.py              # MPVBackend & VLCBackend implementations
│   │   └── player.py                # AudioPlayerAdapter facade & engine selector
│   ├── database/                    # Tortoise ORM SQLite database adapter
│   │   ├── config.py                # Tortoise ORM configuration dict (Aerich support)
│   │   ├── manager.py               # TortoiseStorageAdapter async CRUD implementation
│   │   ├── tables.py                # ORM models (SongTable, PlaylistTable, PlaylistSongTable, HistoryTable)
│   │   └── migrations/              # Aerich migration schema files
│   ├── system/                      # OS adapters & environment helpers
│   │   ├── engine_installer.py      # System package manager auto-installer (apt, pacman, dnf, brew, choco)
│   │   ├── environment_detector.py # Audio engine, JS runtime, browser, and terminal detector
│   │   ├── package_updater.py       # Git/uv auto-updater
│   │   └── paths.py                 # Centralized XDG paths via platformdirs
│   ├── config_manager.py            # JSON-based ConfigPort implementation (ConfigManager)
│   ├── i18n.py                      # Multilingual localization support (t(), set_locale - en/pt)
│   ├── logging.py                   # Centralized logger setup (rotating file handler)
│   └── youtube.py                   # YouTubeMediaProvider (yt-dlp wrapper for search & audio extraction)
└── interface/                       # Presentation layer
    ├── cli/                         # Typer CLI framework
    │   └── commands/                # Subcommands: doctor, log, setup, update, version
    └── tui/                         # Textual TUI interface
        ├── app.py                   # MuPlayer main Textual App class & layout composition
        ├── helpers.py               # Time & formatting utilities
        ├── style.tcss               # Global application CSS stylesheet
        ├── mixins/                  # Controller mixins (NavigationMixin, PlaybackMixin, SearchMixin, base)
        ├── modals/                  # Modals & popup dialogs
        │   ├── configurations/      # Settings modal (theme, language, audio engine)
        │   ├── select_playlist/     # Add-to-playlist picker modal
        │   └── terminal_too_small/  # Responsive screen blocker for small windows (< 80x24)
        ├── views/                   # Main view panels (switched via ContentSwitcher)
        │   ├── home_view/           # Home dashboard & quick navigation view
        │   ├── discover_view/       # Trending / discovery view
        │   └── search_view/         # YouTube search input & results view
        └── widgets/                 # Reusable UI components
            ├── header/              # Top application header widget
            ├── miniplayer/          # Bottom playback bar with progress slider & volume
            ├── sidebar/             # Left navigation & playlist list sidebar
            ├── song_item/           # Individual track row widget
            └── song_list/           # Scrollable track listing widget
```

### Key Navigation Links & Core Files
* **Composition Root / Entry point:** [main.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/main.py)
* **Domain Models:** [models.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/domain/models.py) | [state.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/domain/state.py) | [config.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/domain/config.py)
* **Application Services:** [playback_service.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/application/playback_service.py) | [library_service.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/application/library_service.py) | [search_service.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/application/search_service.py) | [config_service.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/application/config_service.py)
* **Adapters:** [player.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/infrastructure/audio/player.py) | [manager.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/infrastructure/database/manager.py) | [youtube.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/infrastructure/youtube.py) | [config_manager.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/infrastructure/config_manager.py)
* **TUI App & Layout:** [app.py](file:///home/vinicius/Projects/MuPlayer/src/muplayer/interface/tui/app.py) | [style.tcss](file:///home/vinicius/Projects/MuPlayer/src/muplayer/interface/tui/style.tcss)

---

## ⌨️ 4. Default TUI Keybindings

| Keybinding | Action | Description |
| :--- | :--- | :--- |
| `space` | `toggle_play` | Toggle Play / Pause |
| `ctrl+up` | `volume_up` | Increase volume (+5%) |
| `ctrl+down` | `volume_down` | Decrease volume (-5%) |
| `ctrl+right` | `next_track` | Skip to next track in queue |
| `ctrl+left` | `prev_track` | Return to previous track or track start |
| `s` | `toggle_shuffle` | Toggle Shuffle mode |
| `r` | `toggle_repeat` | Toggle Repeat mode |
| `a` | `add_to_playlist` | Open modal to add active song to a playlist |

---

## ⚙️ 5. Subsystems Overview

1. **Composition Root (`main.py`)**: Entry point defining the Typer CLI app. Validates system environment (audio engines, interactive terminal TTY/color capabilities, JavaScript runtime for `yt-dlp`), wires dependency injection, boots the Textual TUI app, and guarantees safe asynchronous resource teardown in `finally`.
2. **Audio Subsystem (`infrastructure/audio`)**: `AudioPlayerAdapter` wraps `mpv` (`MPVBackend`) with dynamic fallback to `vlc` (`VLCBackend`). Streams audio URLs in-memory without downloading media files.
3. **YouTube Media Subsystem (`infrastructure/youtube`)**: `YouTubeMediaProvider` implements `SearchPort` and `MediaPort` using `yt-dlp` and `installed-browsers` (for extracting cookie sessions when available) + JS runtime (`quickjs`, `node`, `deno`, or `bun`). Results are cached by `SearchService` (5 min TTL) and `PlaybackService` (1h TTL).
4. **Database & Persistence (`infrastructure/database`)**: `TortoiseStorageAdapter` manages async `Tortoise ORM` SQLite schema initialization and CRUD for songs (`SongTable`), custom playlists (`PlaylistTable`), track order (`PlaylistSongTable`), and listening history (`HistoryTable`) in `app_data.db`.
5. **Configuration Subsystem (`infrastructure/config_manager.py`, `application/config_service.py`)**: Manages `config.json` via Pydantic `AppConfig`. Synchronizes volume, active Textual theme (e.g. `rose-pine-moon`, `nord`), search limits, and runtime UI language (`en`, `pt`) via `set_locale()`.
6. **TUI Application (`interface/tui`)**: `MuPlayer` inherits from `PlaybackMixin`, `SearchMixin`, and `NavigationMixin`. Composed of views (`HomeView`, `DiscoverView`, `SearchView`), modals (`Configurations`, `SelectPlaylistModal`, `TerminalTooSmallScreen`), and widgets (`Header`, `MiniPlayer`, `Sidebar`, `SongList`, `SongItem`). Enforces minimum terminal size (80x24).
7. **System & Environment (`infrastructure/system`)**: Detects engine shared libraries (`libmpv`/`libvlc`), interactive TTY/ANSI terminal capabilities, resolves XDG paths via `platformdirs`, performs package updates, and auto-installs missing packages using system package managers (`apt`, `pacman`, `dnf`, `brew`, `choco`, `scoop`).

---

## 🛠️ 6. Development & Validation Commands

All commands MUST be executed using `uv`:

```bash
# Install dependencies
uv sync

# Run application (TUI)
uv run muplayer

# Run CLI subcommands
uv run muplayer doctor
uv run muplayer setup
uv run muplayer log
uv run muplayer update
uv run muplayer version

# Run linter and auto-fix code style
uv run ruff check --fix src/

# Format code
uv run ruff format src/

# Run test suite
uv run pytest

# Detect dead code
uv run deadcode src
```

---

## 📍 7. Quick Extension Guide

* **Add CLI Command:** Create `src/muplayer/interface/cli/commands/new_cmd.py` and register it in `src/muplayer/interface/cli/commands/__init__.py`.
* **Add TUI View:** Create `src/muplayer/interface/tui/views/new_view/` (`new_view.py` and `new_view.tcss`) and export it in `src/muplayer/interface/tui/views/__init__.py`.
* **Add TUI Modal:** Create `src/muplayer/interface/tui/modals/new_modal/` (`new_modal.py` and `new_modal.tcss`) and export it in `src/muplayer/interface/tui/modals/__init__.py`.
* **Add TUI Widget:** Create `src/muplayer/interface/tui/widgets/new_widget/` (`new_widget.py` and `new_widget.tcss`) and export it in `src/muplayer/interface/tui/widgets/__init__.py`.
* **Add TUI Mixin / Keybinding:** Add logic in `src/muplayer/interface/tui/mixins/` and bind the shortcut in `MuPlayer.BINDINGS` (`src/muplayer/interface/tui/app.py`).
* **Add Application Service / Port:** Define port protocol in `src/muplayer/application/ports/` and implement the use case service in `src/muplayer/application/`.
* **Add Infrastructure Module:** Create `src/muplayer/infrastructure/new_module/` with an `__init__.py` exporting public symbols.
