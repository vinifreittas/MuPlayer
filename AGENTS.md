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

* **Domain (`domain/`)**: Pure core models & state. CANNOT import from any other layer.
* **Application (`application/`)**: Orchestrates use cases & abstract ports. Imports ONLY from `domain`.
* **Infrastructure (`infrastructure/`)**: Concrete engine adapters. Imports from `domain` and `application`.
* **Interface (`interface/`)**: Presentation layer (TUI/CLI). Imports from `domain`, `application`, and `infrastructure` (via composition root).

### Data & Execution Flow Pattern
`User Input (TUI/CLI)` ➔ `Controller Mixin` ➔ `Application Service` ➔ `Infrastructure Port` ➔ `Adapter Engine (mpv/yt-dlp/Tortoise)` ➔ `Reactive State` ➔ `Textual Widget UI`

---

## 🗺️ 3. Repository Directory Map

```
src/muplayer/
├── __main__.py                      # Entry point delegating to main.py
├── main.py                          # Main Component: Application Composition Root & App Launcher
├── domain/                          # Domain layer
│   ├── config.py                    # AppConfig Pydantic configuration model
│   ├── models.py                    # Song, Playlist Pydantic schemas
│   └── state.py                     # QueueState (tracks, index, active song)

├── application/                     # Application layer (pure use cases & ports)
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

### Key Navigation Links
* **Entry point:** `main.py`
* **Domain models:** `config.py` | `models.py` | `state.py`
* **Services:** `playback_service.py` | `library_service.py` | `search_service.py`
* **Adapters:** `player.py` | `manager.py` | `search.py`
* **TUI App:** `app.py` | `style.tcss`

---

## ⚙️ 4. Subsystems Overview

1. **Main Component & Composition Root (`main.py`)**: Entry point defining the Typer CLI app. Validates system environment (audio engines, terminal interactive TTY/color capabilities, JavaScript runtime for `yt-dlp`), wires dependency injection, boots the Textual TUI app, and guarantees safe resource teardown (`finally`).
2. **Audio Subsystem (`infrastructure/audio`)**: `PlayerAPI` wraps `mpv` (`MPVBackend`) with dynamic fallback to `vlc` (`VLCBackend`). Streams via `yt-dlp` extracted audio URLs (1h TTL cached).
3. **Search Subsystem (`infrastructure/search`)**: `SearchAPI` uses `yt-dlp` to query YouTube videos. Requires a JS runtime (`quickjs`, `node`, `deno`, or `bun`). Results are cached for 5 min by `SearchService`.
4. **Database (`infrastructure/database`)**: `DatabaseManager` manages async `Tortoise ORM` SQLite schema initialization and CRUD for songs and playlists (`app_data.db`).
5. **TUI Application (`interface/tui`)**: `MuPlayer` app inherits from `PlaybackMixin`, `SearchMixin`, and `NavigationMixin`. Uses Textual reactive state properties for UI updates.
6. **System & Environment (`infrastructure/system`)**: Checks audio engine shared libraries (`libmpv`/`libvlc`), interactive TTY/ANSI terminal capabilities, resolves XDG paths via `platformdirs`, performs package updates, and auto-installs missing packages using system package managers (`apt`, `pacman`, `dnf`, `brew`, `choco`, `scoop`).

---

## 🛠️ 5. Development & Validation Commands

All commands MUST be executed using `uv`:

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

## 🔄 7. AI Agent Execution Lifecycle

When executing tasks in this repository, follow this 4-step lifecycle:

1. **Understand & Inspect**: Inspect relevant files before making changes. Never guess file paths, symbol names, or imports.
2. **Surgical Modification**: Modify only target lines and modules needed for the task. Keep changes minimal, lean, and readable.
3. **Mandatory Verification Protocol**: Run static check (`uv run ruff check --fix src/`), format (`uv run ruff format src/`), and test suite (`uv run pytest`).
4. **Documentation Sync**: If architectural patterns, CLI commands, or file structures change, update `AGENTS.md` immediately.

---

## 🎯 8. Non-Negotiable Operational Rules for AI Agents

All AI agents working on MuPlayer MUST strictly obey these 7 core principles:

### 1. Strict Clean Architecture Enforcement
* **Rule**: Respect layer boundaries at all times (`domain` ← `application` ← `infrastructure` / `interface`).
* **DO**: Keep `domain` pure and completely free of external dependencies.
* **NEVER**: Import `infrastructure` or `interface` modules into `domain` or `application`.

### 2. Pragmatic Simplicity (KISS & YAGNI)
* **Rule**: Solve problems with the minimum necessary code, abstraction, and complexity.
* **DO**: Write explicit, direct code that fulfills the exact requirement.
* **NEVER**: Create generic abstractions, unused wrapper classes, or speculative future-proofing logic.

### 3. Zero Tolerance for Ambiguity
* **Rule**: Require exact clarity before modifying logic or contracts.
* **DO**: Stop and ask the user for clarification if instructions, edge cases, or API specifications are unclear.
* **NEVER**: Guess unstated business rules, silent fallback behaviors, or ambiguous parameters.

### 4. Surgical Scope & Zero Unrelated Edits
* **Rule**: Restrict modifications strictly to the target task.
* **DO**: Edit only lines and files directly required to fulfill the user request.
* **NEVER**: Perform peripheral refactoring, formatting edits in adjacent code, or auto-reformatting of untouched files.

### 5. Mandatory 3-Step Verification Protocol
* **Rule**: Never declare a task complete without executing verification.
* **DO**: Run the following validation sequence before completing work:
  1. `uv run ruff check --fix src/` (Static linting & import sorting)
  2. `uv run ruff format src/` (Code formatting)
  3. `uv run pytest` (Unit & integration test suite)
* **NEVER**: Assume code works just because it compiled or was saved to disk.

### 6. Continuous Documentation Maintenance
* **Rule**: Keep repository context always up to date.
* **DO**: Update `AGENTS.md` whenever architectural patterns, conventions, sub-systems, CLI subcommands, or directory structures evolve.
* **NEVER**: Leave documentation out of sync with actual source code.

### 7. Lean, Readable & Self-Explanatory Code
* **Rule**: Source code must be immediately understandable to any human or AI reading it.
* **DO**: Enforce clear, explicit naming and single-responsibility functions.
* **NEVER**: Keep dead code, unused imports, commented-out code blocks, or redundant comments that merely restate what code does.
