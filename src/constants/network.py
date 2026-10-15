from src.sentinels import SENTINELS

SERVER_TIMEOUT = 0.5
BACKLOG = 5
HEADER_LEN = 4
CONNECTION_ENCODING = 'utf-8'
MAX_JSON_SIZE = 10 * 1024 * 1024

SOURCES = {
    SENTINELS.SOURCE_NOT_PROVIDED: '[source not provided]',
    'cli': 'teletypewriter interface (non-interactive)',
    'dash': 'teletypewriter interface (dashboard)',
    'gui': 'graphic user interface',
    'backend': 'backend inter-process communication from backend',
    'player': 'backend inter-process communication from player',
    'hotkey': 'Hotkey control service',
    'tray': 'Tray icon control service',
    'lyric': 'lyric board service service',
    'config_gui': 'configure GUI',
    'process': 'process manager',
    'client': 'client-side network manager',
}

ACK = {
    'msg': 'Copy that'
}

NON_ACTION_KEYS = {
    'action',
    'cwd',
    'source',
    'token',
    'silent',
    'notify_support'
}
