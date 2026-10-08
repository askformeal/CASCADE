from platformdirs import PlatformDirs
from importlib.resources import files
from pathlib import Path

def get_res(filename):
    return str(files('res') / filename)

LICENSE = get_res('license.txt')

ICON = get_res('icon.ico')
ERROR_ICON = get_res('icon_error.ico')
LYRIC_ICON = get_res('lyric_icon.ico')
NO_COVER = get_res('no_cover.txt')
REMOTE_ICON = get_res('config_gui/remote.png')
REFRESH_ICON = get_res('config_gui/refresh.png')
EDIT_ICON = get_res('config_gui/edit.png')
OPEN_FILE_ICON = get_res('config_gui/open_file.png')
COPY_PATH_ICON = get_res('config_gui/copy.png')
COLOR_BLACK_ICON = get_res('config_gui/color_black.png')
COLOR_WHITE_ICON = get_res('config_gui/color_white.png')

GUI_NO_COVER = get_res('gui/no_cover.png')

INFO_ICON = get_res('gui/info.png')
SAVE_COVER_ICON = get_res('gui/save_cover.png')
RELOAD_ICON = get_res('gui/reload.png')
START_ICON = get_res('gui/start.png')

NEXT_SONG_ICON = get_res('gui/next.png')
PREV_SONG_ICON = get_res('gui/previous.png')
PLAY_ICON = get_res('gui/play.png')
PAUSE_ICON = get_res('gui/pause.png')
STOP_ICON = get_res('gui/stop.png')

UNMUTE_ICON = get_res('gui/unmute.png')
MUTE_ICON = get_res('gui/mute.png')

ONLINE_ICON = get_res('gui/online.png')
OFFLINE_ICON = get_res('gui/offline.png')

SHUFFLE_ICON = get_res('gui/shuffle.png')
LOOP_ICON = get_res('gui/loop.png')
REVERSE_ICON = get_res('gui/reverse.png')
DICE_ICON = get_res('gui/dice.png')

FILTER_ICON = get_res('gui/filter.png')
SELECT_CURRENT_ICON = get_res('gui/select_current.png')
SWITCH_SELECTED_ICON = get_res('gui/switch_selected.png')

ONLINE_LYRIC_ICON = get_res('gui/online_lyric.png')
LOCAL_LYRIC_ICON = get_res('gui/local_lyric.png')

RESET_OFFSET_ICON = get_res('gui/reset_offset.png')

GUI_COPY = get_res('gui/copy.png')

dirs = PlatformDirs('cascade', ensure_exists=True)

DATA_DIR = Path(dirs.user_data_dir)
CONFIG_DIR = Path(dirs.user_config_dir)

PID_PATH = DATA_DIR / 'PID.json'
CONFIG_PATH = CONFIG_DIR / 'config.toml'

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

DATABASE = DATA_DIR / 'cascade.db'
DATABASE_DEV = DATA_DIR / 'cascade-dev.db'