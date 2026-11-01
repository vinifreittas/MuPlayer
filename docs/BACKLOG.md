# 📋 Backlog for version 1.0.0

## 🐛 Terminal and Logs
- [X] Fix log leakage in the terminal.
- [X] Define the minimum terminal size (with automatic adjustment if possible).
- [X] Refactor the history system:
  - Fix history bugs and migrate to a real execution record based on the `SongTable` model.
  - Filter results by the latest occurrence.
- [X] Adjust CLI flags:
  - Remove `--force`.
  - Integrate `--debug` into the `log` command (preserve the complete log at *debug* level and apply filters when displaying it).

## 🎵 Playlists
- [ ] Implement removing a track from a playlist.
- [ ] Implement deleting a playlist.

## 🛠️ Quality and Maintenance
- [ ] Analyze and improve the project's structure and documentation.
- [ ] Ensure cross-platform support and optimal operation.
- [ ] Perform complete tests for all features.
- [ ] Reduce system dependencies by bundling more functionality, making the application easier to use.