from src.types import IterType, StrChoiceList, CONVERTER
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

# 'key name': (type, is_required, default_value)
# literal type: (IterType(element_type), is_required). every element needs to match
ACTION_KEYS = {
    'open': {
        'song': (str, True),
        'type': (StrChoiceList(['song', 'playlist', 'file', 'auto']), False, 'auto')
    },
    'switch': {
        'number': (int, True)
    },
    'prev': {
        'on_end': (CONVERTER.boolean, False, False)
    },
    'next': {
        'on_end': (CONVERTER.boolean, False, False)
    },
    'seek': {
        'time': (str, True),
        'ms': (CONVERTER.boolean, False, False)
    },
    'jump': {
        'progress': (int, True)
    },
    'volume': {
        'volume': (str, True)
    },
    'set_offset_overlay': {
        'offset': (int, True),
        'autoincrement': (CONVERTER.boolean, False, False)
    },
    'lib.info':
    {
        'songs': (IterType(str), True),
        'show_aliases': (CONVERTER.boolean, False, False),
        'show_playlists': (CONVERTER.boolean, False, False),
        'force_id': (CONVERTER.boolean, False, False)
    },
    'lib.list': {
        'show_aliases': (CONVERTER.boolean, False, False),
        'show_playlists': (CONVERTER.boolean, False, False),
        'show_tech': (CONVERTER.boolean, False, False)
    },
    'lib.search': {
        'keyword': (IterType(str), True),
        'or': (CONVERTER.boolean, False, False)
    },
    'lib.add': {
        'paths': (IterType(str), True),
        'aliases': (IterType(str), False, []),
        'skip_meta': (CONVERTER.boolean, False, False),
        'skip_alias': (CONVERTER.boolean, False, False),
        'skip_lyric': (CONVERTER.boolean, False, False),
        'loose_path': (CONVERTER.boolean, False, False)
    },
    'lib.del': {
        'songs': (IterType(str), True)
    },
    'lib.prune':
    {
        'dry_run': (CONVERTER.boolean, False, False),
    },
    'lib.scan': {
        'dir': (str, True),
        'playlist': (str, False, None),
        'recurse': (CONVERTER.boolean, False, False),
        'dry_run': (CONVERTER.boolean, False, False),
        'skip_meta': (CONVERTER.boolean, False, False),
        'skip_alias': (CONVERTER.boolean, False, False),
        'skip_lyric': (CONVERTER.boolean, False, False),
    },
    'lib.meta.set': {
        'song': (str, True),
        'name': (str, False, None),
        'artist': (str, False, None),
        'album': (str, False, None),
        'duration': (int, False, None),
        'bitrate': (int, False, None),
        'sample_rate': (int, False, None),
        'channels': (int, False, None),
        'lyric': (str, False, None),
        'offset': (int, False, None),
    },

    'lib.meta.read-file': {
        'song': (str, True),
        'name': (CONVERTER.boolean, False, False),
        'artist': (CONVERTER.boolean, False, False),
        'album': (CONVERTER.boolean, False, False),
        'duration': (CONVERTER.boolean, False, False),
        'bitrate': (CONVERTER.boolean, False, False),
        'sample_rate': (CONVERTER.boolean, False, False),
        'channels': (CONVERTER.boolean, False, False),
        'all': (CONVERTER.boolean, False, False),
    },

    'lib.alias.list': {
        'song': (str, True)
    },
    'lib.alias.bind': {
        'song': (str, True),
        'aliases': (IterType(str), True)
    },
    'lib.alias.unbind': {
        'aliases': (IterType(str), True)
    },
    'lib.lyric.set':
    {
        'song': (str, True),
        'path': (str, True)
    },
    'lib.lyric.show':
    {
        'song': (str, True)
    },
    'lib.lyric.fetch':
    {
        'songs': (IterType(str), True)
    },
    'lib.lyric.offset':
    {
        'song': (str, True),
        'offset': (int, True)
    },
    'lib.playlist.list': {
        'playlist': (str, False, None),
        'show_aliases': (CONVERTER.boolean, False, False),
        'show_playlists': (CONVERTER.boolean, False, False),
        'show_tech': (CONVERTER.boolean, False, False)
    },
    'lib.playlist.create': {
        'name': (str, True)
    },
    'lib.playlist.add': {
        'playlist': (str, True),
        'songs': (IterType(str), True)
    },
    'lib.playlist.kick': {
        'playlist': (str, True),
        'songs': (IterType(str), True)
    },
    'lib.playlist.del': {
        'playlist': (str, True)
    },
    'lib.playlist.swap': {
        'playlist': (str, True),
        'song1': (str, True),
        'song2': (str, True)
    },
    'lib.playlist.move': {
        'playlist': (str, True),
        'song': (str, True),
        'position': (int, True)
    },
    'config.show': {
        'option': (str, True)
    },
    'config.set': {
        'option': (str, True),
        'value': (str, True),
        'overwrite_corrupt': (CONVERTER.boolean, False, False)
    },
    'config.unset': {
        'option': (str, True)
    },
}

NON_ACTION_KEYS = {
    'action',
    'cwd',
    'source',
    'token',
    'silent',
    'notify_support'
}
