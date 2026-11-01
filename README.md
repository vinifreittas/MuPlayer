# 🎵 MuPlayer

**MuPlayer** is a lightweight and efficient terminal-based audio player (TUI), turning YouTube into your personal streaming service. It is designed for developers and command-line enthusiasts who want to listen to music and podcasts without browser distractions or excessive memory usage.

It uses `yt-dlp` for search and stream URL extraction, `mpv` or `vlc` for continuous audio playback, the `Textual` framework for its rich TUI, and `SQLite` (via Tortoise ORM) for local library and playlist management.

---

## ✨ Main Features and Qualities

* **Lightweight and Fast:** Minimal CPU and RAM usage (without browser overhead).
* **Direct Streaming:** Instant audio playback streamed entirely in memory, with no prior download required.
* **Modern TUI:** Responsive interface built with Textual, keyboard shortcuts (Vim-style and media keys), visual themes (Spotify Dark), and MiniPlayer.
* **Complete Local Library:** Management of custom playlists, saved/favorite tracks, and playback history through SQLite.
* **Fast Import:** Import public YouTube playlists directly from a link/URL.
* **Smart Diagnostics and Fallback:** Automatic dependency detection at startup and dynamic switching between audio engines (`mpv` and `vlc`).

---

## 📋 System Requirements

### System Dependencies

| Dependency | Options |
| :--- | :--- |
| **Audio Engine** | `mpv` *(recommended)* or `vlc` |
| **JavaScript Runtime** | `quickjs`, `node`, `deno` ou `bun` |
| **Compatible Terminal** | Color and interactive TTY support |
| **Web Browser** | Chrome, Firefox, Brave, etc. *(used by yt-dlp for cookie extraction)* |

> 💡 *Run `muplayer setup` to install system dependencies automatically, or `muplayer doctor` to check the environment.*

### Python Dependencies

Python `>= 3.12` and the [uv](https://docs.astral.sh/uv/) package manager must be installed. All Python libraries are managed automatically by `uv`.

---

## 🚀 Installation and Usage with `uv`

**MuPlayer** is designed to be managed and run exclusively with `uv`.

### 1. Installation (Global Tool)

Install MuPlayer as a global terminal tool with `uv tool`:

```bash
uv tool install git+https://github.com/vinifreittas/MuPlayer.git
```

### 2. Initial Setup (Interactive Assistant)

Run the diagnostic assistant to check and guide the installation of system dependencies:

```bash
# If installed via uv tool:
muplayer setup

# In a local development environment (repository clone):
uv run muplayer setup
```

### 3. Start the Player

After the initial setup, start the TUI player:

```bash
# If installed via uv tool:
muplayer

# In local development:
uv run muplayer
```

---

## 🛠️ CLI Commands

MuPlayer provides a complete set of Typer commands (available through `muplayer <command>` or `uv run muplayer <command>`):

| Command | Description |
| :--- | :--- |
| `muplayer` | Starts the player's main TUI. |
| `muplayer setup` | Runs the interactive assistant for installing audio engines and system dependencies. |
| `muplayer doctor` | Displays a complete system diagnosis (terminal, audio engines, JS runtime, and XDG directories). |
| `muplayer log` | Displays saved system logs (use `--debug` or `-d` to show debug records). |
| `muplayer update` | Checks for and installs the latest MuPlayer version from the repository. |
| `muplayer version` | Displays the current application version. |

---

## 📁 Storage and Configuration (XDG Standard)

MuPlayer data is stored in standard operating system directories managed by `platformdirs`:

* **Database and Configuration:** `~/.local/share/MuPlayer/` (`app_data.db`, `config.json`)
* **Search and URL Cache:** `~/.cache/MuPlayer/` (5-minute search cache and 1-hour stream URL cache)
* **System Logs:** `~/.local/state/MuPlayer/logs/`

---

## 🛠️ Technologies Used

* **[Textual](https://textualize.io):** Terminal user interface (TUI) framework.
* **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** YouTube audio stream search and extraction.
* **[mpv](https://mpv.io) / [VLC](https://www.videolan.org):** High-fidelity audio playback engines.
* **[Tortoise ORM](https://tortoise.github.io) & [SQLite](https://www.sqlite.org):** Asynchronous persistence for the local library and playlists.
* **[Typer](https://typer.tiangolo.com) & [Rich](https://rich.readthedocs.io):** Command-line interface (CLI) framework and report formatting.