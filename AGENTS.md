# 🤖 AGENTS.md — AI Agent Guidelines for MuPlayer

This document provides high-level architectural context, coding conventions, repository navigation, and operational rules for AI agents working in the **MuPlayer** repository.

---

## 📌 1. Project Overview & Tech Stack

**MuPlayer** is a lightweight, efficient terminal-based audio player (TUI) streaming YouTube audio.

* **Language:** Python >= 3.12 (managed via `uv`)
* **TUI Interface:** [Textual](https://textualize.io) (CSS-styled, reactive widgets, screens, themes)
* **CLI Framework:** [Typer](https://typer.tiangolo.com) + [Rich](https://rich.readthedocs.io)
* **Audio Engine:** `mpv` (`python-mpv`) with fallback to `vlc` (`python-vlc`)
* **Streaming & Search:** `yt-dlp` (requires system JavaScript runtime: `quickjs`, `node`, `deno`, or `bun`)
* **Database & Cache:** `SQLite` via `Tortoise ORM` | `diskcache` for response caching
* **Tooling:** `ruff` (linter/formatter), `pytest` / `pytest-asyncio` (testing), `deadcode`

### Standard XDG Directory Structure (`platformdirs`)
* **Data (DB & Config):** `~/.local/share/MuPlayer/` (`app_data.db`, `config.json`)
* **Cache:** `~/.cache/MuPlayer/`
* **Logs:** `~/.local/state/MuPlayer/logs/`

---

## 🏗️ 2. Clean Architecture & System Data Flow

MuPlayer strictly follows **Layered Clean Architecture**:

```
src/muplayer/
├── domain/           # Pure entities (Song, Playlist) & state (QueueState). No external dependencies.
├── application/      # Use case orchestrators (Playback, Search, Library), Composition Root & Ports.
├── infrastructure/   # Adapters (Audio, Search, Database, System, Cache, Config, i18n, Logging).
└── interface/        # Presentation layer: CLI commands and Textual TUI (app, mixins, widgets, screens).
```

### ⚠️ The Golden Dependency Rule
```
domain  ←  application  ←  infrastructure
                         ←  interface
```

### Data & Execution Flow Pattern
`User Input (TUI/CLI)` ➔ `Controller Mixin` ➔ `Application Service` ➔ `Infrastructure Port` ➔ `Adapter Engine (mpv/yt-dlp/Tortoise)` ➔ `Reactive State` ➔ `Textual Widget UI`

---

## 🗺️ 3. Repository Directory Map

```
src/muplayer/
├── __main__.py                      # Entry point (CLI parser / TUI launcher)
├── domain/                          # Domain layer
│   ├── models.py                    # Song, Playlist Pydantic schemas
│   └── state.py                     # QueueState (tracks, index, active song)
├── application/                     # Application layer
│   ├── bootstrap.py                 # Composition Root & environment pre-flight validator
│   ├── library_service.py           # Playlist/library management service
│   ├── playback_service.py          # Playback & queue control logic
│   ├── search_service.py            # Search orchestration service with caching
│   └── ports/                       # Abstract protocols (AudioPort, SearchPort, StoragePort, ConfigPort)
├── infrastructure/                  # Infrastructure adapters
│   ├── audio/                       # Audio engine adapter
│   │   ├── backends.py              # MPVBackend & VLCBackend implementations
│   │   └── player.py                # PlayerAPI facade & engine selector
│   ├── database/                    # Tortoise ORM database adapter
│   │   ├── config.py                # Tortoise ORM configuration dict
│   │   ├── manager.py               # DatabaseManager async initialization & CRUD
│   │   ├── tables.py                # Tortoise ORM models (SongTable, PlaylistTable)
│   │   └── migrations/              # Aerich migration schema files
│   ├── system/                      # OS adapters & environment helpers
│   │   ├── engine_installer.py      # System package manager auto-installer (apt, brew, pacman, etc.)
│   │   ├── environment_detector.py # Audio engine & terminal capability detector
│   │   ├── package_updater.py       # Git/pip auto-updater
│   │   └── paths.py                 # Centralized XDG paths via platformdirs
│   ├── config.py                    # Config file manager (ConfigManager)
│   ├── i18n.py                      # Multilingual support (t(), set_locale)
│   ├── logging.py                   # Centralized logger setup
│   └── search.py                    # Search API (yt-dlp wrapper & stream URL extraction)
└── interface/                       # Presentation layer
    ├── cli/                         # Typer CLI framework
    │   ├── main.py                  # Main Typer app & callback handler
    │   └── commands/                # Subcommands (doctor, setup, update, version)
    └── tui/                         # Textual TUI interface
        ├── app.py                   # MuPlayer main Textual App class
        ├── helpers.py               # Time & formatting utilities
        ├── style.tcss               # CSS stylesheet for Textual widgets
        ├── controllers/             # Mixins (PlaybackMixin, SearchMixin, NavigationMixin)
        ├── screens/                 # Screens & Modals (ConfigurationsScreen, SelectPlaylistModal)
        ├── themes/                  # Custom color themes (Spotify Dark)
        └── widgets/                 # Reactive UI components (Header, MiniPlayer, Sidebar, SongList)
```

---

## ⚙️ 4. Subsystems Overview

1. **Bootstrap & Composition Root (`application/bootstrap.py`)**: Validates system environment (audio engines, terminal interactive TTY/color capabilities, JavaScript runtime for `yt-dlp`), wires dependency injection, boots the Textual app, and guarantees safe resource teardown (`finally`).
2. **Audio Subsystem (`infrastructure/audio`)**: `PlayerAPI` wraps `mpv` (`MPVBackend`) with dynamic fallback to `vlc` (`VLCBackend`). Streams via `yt-dlp` extracted audio URLs (1h TTL cached).
3. **Search Subsystem (`infrastructure/search`)**: `SearchAPI` uses `yt-dlp` to query YouTube videos. Requires a JS runtime (`quickjs`, `node`, `deno`, or `bun`). Results are cached for 5 min by `SearchService`.
4. **Database (`infrastructure/database`)**: `DatabaseManager` manages async `Tortoise ORM` SQLite schema initialization and CRUD for songs and playlists (`app_data.db`).
5. **TUI Application (`interface/tui`)**: `MuPlayer` app inherits from `PlaybackMixin`, `SearchMixin`, and `NavigationMixin`. Uses Textual reactive state properties for UI updates.
6. **System & Environment (`infrastructure/system`)**: Checks audio engine shared libraries (`libmpv`/`libvlc`), interactive TTY/ANSI terminal capabilities, resolves XDG paths via `platformdirs`, performs package updates, and auto-installs missing packages using system package managers (`apt`, `pacman`, `dnf`, `brew`, `choco`, `scoop`).

---

## 🛠️ 5. Development & Validation Commands

All commands must be executed using `uv`:

```bash
# Install dependencies
uv sync

# Run application (TUI)
uv run muplayer

# Run CLI subcommands
uv run muplayer doctor
uv run muplayer setup

# Run linter and auto-fix code style (ALWAYS use --fix)
uv run ruff check --fix src/

# Format code
uv run ruff format src/

# Run test suite
uv run pytest

# Detect dead code
uv run deadcode src
```

---

## 📍 6. Quick Extension Guide

* **Add CLI Command:** Create `src/muplayer/interface/cli/commands/new_cmd.py` and register it in `src/muplayer/interface/cli/commands/__init__.py`.
* **Add TUI Widget:** Create in `src/muplayer/interface/tui/widgets/` and export in `__init__.py`.
* **Add TUI Screen/Modal:** Create in `src/muplayer/interface/tui/screens/` and export in `__init__.py`.
* **Add TUI Controller/Keybinding:** Add logic to appropriate Mixin in `src/muplayer/interface/tui/controllers/` and bind key in `MuPlayer.BINDINGS` (`app.py`).
* **Add Infrastructure Module:** Create `src/muplayer/infrastructure/new_module/` with an `__init__.py` exporting public symbols.

---

## 🎯 7. Non-Negotiable Operational Rules for Agents

Any AI agent working on MuPlayer must strictly adhere to these 5 rules:

### 1. Pragmatic Simplicity (KISS)
* Solve problems with the minimum necessary code, abstraction, and complexity.
* Avoid over-engineering. NEVER create generic abstractions or unnecessary helper utilities for simple tasks.

### 2. Zero Tolerance for Ambiguity
* Never assume requirements, business logic, architectures, or unstated behaviors.
* If instructions or contracts are unclear, **STOP IMMEDIATELY** and ask for clarification.

### 3. Surgical Scope
* Keep focus strictly restricted to the requested task. Modify only target files and lines.
* NEVER perform peripheral refactoring, formatting edits in adjacent code, or modifications outside the target module.

### 4. Double-Check Verification Protocol
* Verify delivery before completing:
  1. Does the diff strictly address the requested scope?
  2. Are syntax, typing, and imports correct?
  3. Was static verification executed with `uv run ruff check --fix src/`?
  4. Were existing features or tests unintentionally broken?

### 5. Continuous Documentation Maintenance (Keep AGENTS.md Updated)
* Always keep `AGENTS.md` updated whenever architectural patterns, conventions, commands, or workflows evolve.
