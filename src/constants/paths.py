from platformdirs import PlatformDirs
from importlib.resources import files
from pathlib import Path

def get_res(filename):
    return str(files('res') / filename)

LICENSE_PATH = get_res('license.txt')

ICON_PATH = get_res('icon.ico')
ERROR_ICON_PATH = get_res('icon_error.ico')
LYRIC_ICON_PATH = get_res('lyric_icon.ico')
NO_COVER_PATH = get_res('no_cover.txt')
REMOTE_ICON_PATH = get_res('config_gui/remote.png')
REFRESH_ICON_PATH = get_res('config_gui/refresh.png')
EDIT_ICON_PATH = get_res('config_gui/edit.png')
OPEN_FILE_ICON_PATH = get_res('config_gui/open_file.png')
COPY_PATH_ICON_PATH = get_res('config_gui/copy.png')
COLOR_BLACK_ICON_PATH = get_res('config_gui/color_black.png')
COLOR_WHITE_ICON_PATH = get_res('config_gui/color_white.png')

GUI_NO_COVER_PATH = get_res('gui/no_cover.png')

NEXT_SONG_ICON_PATH = get_res('gui/next.png')
PREV_SONG_ICON_PATH = get_res('gui/previous.png')
PLAY_ICON_PATH = get_res('gui/play.png')
PAUSE_ICON_PATH = get_res('gui/pause.png')
STOP_ICON_PATH = get_res('gui/stop.png')

UNMUTE_ICON_PATH = get_res('gui/unmute.png')
MUTE_ICON_PATH = get_res('gui/mute.png')

ONLINE_ICON_PATH = get_res('gui/online.png')
OFFLINE_ICON_PATH = get_res('gui/offline.png')

SHUFFLE_ICON_PATH = get_res('gui/shuffle.png')
LOOP_ICON_PATH = get_res('gui/loop.png')
DICE_ICON_PATH = get_res('gui/dice.png')

SELECT_CURRENT_ICON_PATH = get_res('gui/select_current.png')
SWITCH_SELECTED_ICON_PATH = get_res('gui/switch_selected.png')

ONLINE_LYRIC_ICON_PATH = get_res('gui/online_lyric.png')
LOCAL_LYRIC_ICON_PATH = get_res('gui/local_lyric.png')

RESET_OFFSET_ICON_PATH = get_res('gui/reset_offset.png')

dirs = PlatformDirs('cascade', ensure_exists=True)

DATA_DIR = Path(dirs.user_data_dir)
CONFIG_DIR = Path(dirs.user_config_dir)

PID_PATH = DATA_DIR / 'PID.json'
CONFIG_PATH = CONFIG_DIR / 'config.toml'

LOG_DIR = Path(dirs.user_log_dir)
BACKEND_LOG_PATH = LOG_DIR / 'cascade.log'
SOCKET_LOG_PATH = LOG_DIR / 'cascade-socket.log'
CLI_LOG_PATH = LOG_DIR / 'cascade-cli.log'
HOTKEY_LOG_PATH = LOG_DIR / 'cascade-hotkey.log'
TRAY_LOG_PATH = LOG_DIR / 'cascade-tray.log'
LYRIC_LOG_PATH = LOG_DIR / 'cascade-lyric.log'
DASH_LOG_PATH = LOG_DIR / 'cascade-dash.log'
GUI_LOG_PATH = LOG_DIR / 'cascade-gui.log'
CONFIG_GUI_LOG_PATH = LOG_DIR / 'cascade-config-gui.log'
CONFIG_LOG_PATH = LOG_DIR / 'cascade-config.log'
PID_LOG_PATH = LOG_DIR / 'cascade-pid.log'
UTIL_LOG_PATH = LOG_DIR / 'cascade-util.log'

DATABASE_PATH = DATA_DIR / 'cascade.db'
DATABASE_DEV_PATH = DATA_DIR / 'cascade-dev.db'