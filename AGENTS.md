# AGENTS.md

CASCADE is a CLI music player for Windows: one background daemon (`cascade start`) plus several frontends (CLI, dashboard TUI, tkinter GUI, config GUI, tray icon, floating lyric board, media-key hotkey) that talk to the daemon over local socket IPC.

Everything here is project-specific. User-facing behaviour lives in `docs/`, version history in `CHANGELOG.md`.

## Commands

Always run from the repo root with the project venv. Never use the global Python.

- Run the CLI: `./venv/Scripts/python.exe -m src <command>`
- Run all tests: `./venv/Scripts/python.exe -m pytest`
- Run one file / one test: `./venv/Scripts/python.exe -m pytest tests/test_backend.py -xvs` / `... tests/test_backend.py::test_name`
- Start / stop the daemon: `./venv/Scripts/python.exe -m src start [module]` / `... exit`. `<module>` is `backend` (default), `hotkey`, `tray` or `lyric`, so a single background service can be started on its own
- Install deps: `./venv/Scripts/python.exe -m pip install -r requirements-dev.txt`
- Portable build: `bash build.sh` (bundles a standalone interpreter and VLC into `dist/`)
- Release: `./venv/Scripts/bump-my-version.exe bump patch|minor`, commit the two version files, then `git tag vX.Y.Z`

## Testing

- `tests/conftest.py` redirects the database, PID file and config into a temp dir, so tests never touch real user state.
- Backend tests call `dispatch()` directly and never open a socket. After changing the socket or client layer, verify against a real started daemon with a real frontend command.
- When an interface change breaks tests, update the test call sites in the same change.

## Dependencies

`requirements.in` and `requirements-dev.in` are hand-written. The `.txt` files are pip-compile output and are never edited by hand.

## Layout

- `src/backend/` - daemon: `core.py` (socket, lifecycle, dispatch loop), `request.py` (the action table), `handlers/` (one module per action group), `database/` (mixin classes composed into `Database`, one per table group), `playback/` (player state, audio engines, lyric cache), `task.py` (task queue behind the `task` command)
- `src/frontend/` - `cli/`, `dash/`, `gui/`, `config_gui/`, `tkinter_tools/`, plus `client.py` (socket client and dead-backend heartbeat), `snapshot.py`, `cover.py`, `tray.py`, `lyric.py`, `hotkey.py`
- `src/constants/` - a package of constant modules, re-exported from its `__init__.py`
- `src/gen_response.py` (response classes), `src/converters.py` (`IterType`, `Converter`), `src/sentinels.py`, `src/config.py`, `src/config_manager.py`, `src/process.py`, `src/pid.py`, `src/log.py`
- `res/` - icons and images. Only files under `res/` get packaged, per `[tool.setuptools.package-data]`
- `docs/` user documentation, `tests/` pytest suite, `tmp/` scratch space (gitignored)

## Invariants

- Every backend action is declared in `src/backend/request.py`: action to handler, plus its key types. A key name that disagrees between that table and the handler fails silently, so change both in the same edit.
- The dispatch consumer thread must never raise. Anything the loop touches goes inside its try/except, or the daemon stops answering while the socket stays open.
- SQLite is one connection per thread (`threading.local` in `src/backend/database/core.py`). Never hand a connection or cursor to another thread.
- The TUI and GUI frontends share one bare-letter hotkey cluster. Check `DashKeyMap` in `src/constants/dash.py` before claiming a new key.
- Long work belongs in a thread (lyric fetching, library scanning), never in the dispatch loop.
- Background services are spawned by `ProcessManager.spawn()` with a dotted module path (`python -m src.frontend.tray`), so a short name gets a child that dies silently - `spawn()` sends its output to `DEVNULL`. `NAME_TO_MODULE` in `src/constants/cli.py` holds those paths.
- User state (database, logs, `PID.json`, `config.toml`) lives outside the repo, under the platformdirs paths in `src/constants/paths/`.

## Conventions

- English only in code, comments, docs and commit messages.
- No em dash in any written text; use a plain hyphen.
- No ternary expressions, no list comprehensions. Branch with explicit `if`/`elif` chains, and do not end such a chain with a bare `else`.
- `ALL_CAPS` constants, `snake_case` variables and files, `PascalCase` classes. Use `...` instead of `pass` in stubs.
- Comments are short, English, and only where the code does not already say it.

## Git

- Commit messages: conventional prefix, verb phrase, lowercase, no trailing period. No body unless one was asked for. General prefixes are `feat:` / `fix:` / `refactor:` / `docs:` / `chore:`, and a change confined to one frontend takes that frontend's name instead (`dash:`, `gui:`, `cli:`).
- `CHANGELOG.md` records every version. New work goes under `[Unreleased]`, in the subsection for the area or frontend it touches (`#### Overall`, `#### Backend`, `#### CLI`, `#### GUI`, `#### Dashboard`, `#### Tray icon`, `#### Config GUI`). List only what the commit actually contains.
- Commit, tag and push only when explicitly asked. Never commit secrets or `.env`.

## Documentation

Point at these instead of copying them:

- `docs/Index.md` - entry point for all documentation
- `docs/CLI.md` - every command and its flags
- `docs/Features.md`, `docs/Configuration.md`, `docs/File Paths.md`
- `README.md`, `TODO.md`, `CHANGELOG.md`
