from pathlib import Path
from . import dirs

LOG_DIR = Path(dirs.user_log_dir)
BACKEND_LOG = LOG_DIR / 'cascade.log'
SOCKET_LOG = LOG_DIR / 'cascade-socket.log'
CLI_LOG = LOG_DIR / 'cascade-cli.log'
HOTKEY_LOG = LOG_DIR / 'cascade-hotkey.log'
TRAY_LOG = LOG_DIR / 'cascade-tray.log'
LYRIC_LOG = LOG_DIR / 'cascade-lyric.log'
DASH_LOG = LOG_DIR / 'cascade-dash.log'
GUI_LOG = LOG_DIR / 'cascade-gui.log'
CONFIG_GUI_LOG = LOG_DIR / 'cascade-config-gui.log'
CONFIG_LOG = LOG_DIR / 'cascade-config.log'
PID_LOG = LOG_DIR / 'cascade-pid.log'
UTIL_LOG = LOG_DIR / 'cascade-util.log'