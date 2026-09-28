# File Paths

## Configuration

| Platform | Path                                                  |
| -------- | ----------------------------------------------------- |
| Windows  | `%LOCALAPPDATA%\cascade\cascade\config.toml`        |
| Linux    | `~/.config/cascade/config.toml`                     |
| macOS    | `~/Library/Application Support/cascade/config.toml` |

## Log

### Directory

| Platform | Path                                     |
| -------- | ---------------------------------------- |
| Windows  | `%LOCALAPPDATA%\cascade\cascade\Logs\` |
| Linux    | `~/.local/state/cascade/log/`          |
| macOS    | `~/Library/Logs/cascade/`              |

### Filename

| Module           | Filename                   |
| ---------------- | -------------------------- |
| Backend          | `cascade.log`            |
| IPC              | `cascade-socket.log`     |
| Media Key Daemon | `cascade-hotkey.log`     |
| System Tray      | `cascade-tray.log`       |
| Lyric Board      | `cascade-lyric.log`      |
| Dashboard        | `cascade-dash.log`       |
| GUI              | `cascade-gui.log`        |
| Config GUI       | `cascade-config-gui.log` |
| Configure        | `cascade-config.log`     |
| PID Management   | `cascade-pid.log`        |
| Utils            | `cascade-util.log`       |

## Database

| Platform | Path                                                 |
| -------- | ---------------------------------------------------- |
| Windows  | `%LOCALAPPDATA%\cascade\cascade\cascade.db`        |
| Linux    | `~/.local/share/cascade/cascade.db`                |
| macOS    | `~/Library/Application Support/cascade/cascade.db` |

> **Development database is under the same directory, named `cascade-dev.db`**

## PID

| Platform | Path                                               |
| -------- | -------------------------------------------------- |
| Windows  | `%LOCALAPPDATA%\cascade\cascade\PID.json`        |
| Linux    | `~/.local/share/cascade/PID.json`                |
| macOS    | `~/Library/Application Support/cascade/PID.json` |
