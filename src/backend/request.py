from typing import Callable

from src.log import setup_logger
from src.constants.paths.log import BACKEND_LOG
from src.constants.network import NON_ACTION_KEYS
from src.config import CONFIG
from src import gen_response
from src.gen_response import Response
from src.converters import IterType, StrChoiceList, CONVERTER

from .handlers import misc, config, status, poll, task
from .handlers.library import meta, alias, lyric, playlist
from .handlers.library import core as lib_core
from .handlers.playback import sequence, navigation
from .handlers.playback import core as play_core


logger = setup_logger(__name__, BACKEND_LOG)

class Key:
    def __init__(self, name: str, converter: Callable, required: bool, default):
        self.name = name
        self.converter = converter
        self.required = required
        self.default = default

class Command:
    def __init__(self, action: str, handler: Callable):
        self.action = action
        self.handler = handler
        self.keys: list[Key] = []

    def add_key(self, name: str, converter: Callable, required: bool = True, default = None):
        key = Key(name, converter, required, default)
        self.keys.append(key)

class RequestManager:
    def __init__(self):
        self.commands: dict[str, Command] = {}

        # General
        self._add_command('test_alive', misc.test_alive)
        self._add_command('get_notifies', misc.get_notifies)
        self._add_command('status', status.status)
        self._add_command('task', task.task)
        self._add_command('exit', misc.exit_)

        # Playback
        open_ = self._add_command('open', play_core.open_)
        open_.add_key('song', str)
        open_.add_key('type', StrChoiceList(['song', 'playlist', 'file', 'auto']), False, 'auto')

        self._add_command('play_all', play_core.play_all)
        self._add_command('load_last', play_core.load_last)
        self._add_command('stop', play_core.stop)
        self._add_command('pause', play_core.pause)
        self._add_command('resume', play_core.resume)
        self._add_command('toggle', play_core.toggle)
        self._add_command('list', sequence.list_)
        self._add_command('loop', sequence.loop)
        self._add_command('reverse', sequence.reverse)
        self._add_command('shuffle', sequence.shuffle)
        self._add_command('dice', sequence.dice)
        
        switch = self._add_command('switch', sequence.switch)
        switch.add_key('number', int)

        prev = self._add_command('prev', sequence.prev)
        prev.add_key('on_end', CONVERTER.boolean, required=False, default=False)

        next_ = self._add_command('next', sequence.next_)
        next_.add_key('on_end', CONVERTER.boolean, required=False, default=False)

        seek = self._add_command('seek', navigation.seek)
        seek.add_key('time', str)
        seek.add_key('ms', CONVERTER.boolean, required=False, default=False)

        jump = self._add_command('jump', navigation.jump)
        jump.add_key('progress', int)

        self._add_command('replay', navigation.replay)
        
        volume = self._add_command('volume', play_core.volume)
        volume.add_key('volume', str)
        
        self._add_command('mute', play_core.mute)
        self._add_command('reload_lyric', play_core.reload_lyric)
        self._add_command('switch_lyric_mode', play_core.switch_lyric_mode)

        offset = self._add_command('set_offset_overlay', play_core.set_offset_overlay)
        offset.add_key('offset', int)
        offset.add_key('autoincrement', CONVERTER.boolean, required=False, default=False)
        
        self._add_command('get_cover', play_core.get_cover)
        self._add_command('poll', poll.poll)

        # Library
        info = self._add_command('lib.info', lib_core.info)
        info.add_key('songs', IterType(str))
        info.add_key('show_aliases', CONVERTER.boolean, required=False, default=False)
        info.add_key('show_playlists', CONVERTER.boolean, required=False, default=False)
        info.add_key('force_id', CONVERTER.boolean, required=False, default=False)

        list_ = self._add_command('lib.list', lib_core.list_)
        list_.add_key('show_aliases', CONVERTER.boolean, required=False, default=False)
        list_.add_key('show_playlists', CONVERTER.boolean, required=False, default=False)
        list_.add_key('show_tech', CONVERTER.boolean, required=False, default=False)

        search = self._add_command('lib.search', lib_core.search)
        search.add_key('keyword', IterType(str))
        search.add_key('or', CONVERTER.boolean, required=False, default=False)

        add = self._add_command('lib.add', lib_core.add)
        add.add_key('paths', IterType(str))
        add.add_key('aliases', IterType(str), required=False, default=[])
        add.add_key('skip_meta', CONVERTER.boolean, required=False, default=False)
        add.add_key('skip_alias', CONVERTER.boolean, required=False, default=False)
        add.add_key('skip_lyric', CONVERTER.boolean, required=False, default=False)
        add.add_key('loose_path', CONVERTER.boolean, required=False, default=False)

        del_ = self._add_command('lib.del', lib_core.del_)
        del_.add_key('songs', IterType(str))

        prune = self._add_command('lib.prune', lib_core.prune)
        prune.add_key('dry_run', CONVERTER.boolean, required=False, default=False)

        scan = self._add_command('lib.scan', lib_core.scan)
        scan.add_key('dir', str)
        scan.add_key('playlist', str, required=False)
        scan.add_key('recurse', CONVERTER.boolean, required=False, default=False)
        scan.add_key('dry_run', CONVERTER.boolean, required=False, default=False)
        scan.add_key('skip_meta', CONVERTER.boolean, required=False, default=False)
        scan.add_key('skip_alias', CONVERTER.boolean, required=False, default=False)
        scan.add_key('skip_lyric', CONVERTER.boolean, required=False, default=False)

        self._add_command('lib.reset', lib_core.reset)

        # Metadata
        set_meta = self._add_command('lib.meta.set', meta.set_)
        set_meta.add_key('song', str)
        set_meta.add_key('name', str, required=False, default=None)
        set_meta.add_key('artist', str, required=False, default=None)
        set_meta.add_key('album', str, required=False, default=None)
        set_meta.add_key('duration', int, required=False, default=None)
        set_meta.add_key('bitrate', int, required=False, default=None)
        set_meta.add_key('sample_rate', int, required=False, default=None)
        set_meta.add_key('channels', int, required=False, default=None)
        set_meta.add_key('lyric', str, required=False, default=None)
        set_meta.add_key('offset', int, required=False, default=None)

        read_file_meta = self._add_command('lib.meta.read-file', meta.read_file)
        read_file_meta.add_key('song', str)
        read_file_meta.add_key('all', CONVERTER.boolean, required=False, default=False)
        read_file_meta.add_key('name', CONVERTER.boolean, required=False, default=False)
        read_file_meta.add_key('artist', CONVERTER.boolean, required=False, default=False)
        read_file_meta.add_key('album', CONVERTER.boolean, required=False, default=False)
        read_file_meta.add_key('duration', CONVERTER.boolean, required=False, default=False)
        read_file_meta.add_key('bitrate', CONVERTER.boolean, required=False, default=False)
        read_file_meta.add_key('sample_rate', CONVERTER.boolean, required=False, default=False)
        read_file_meta.add_key('channels', CONVERTER.boolean, required=False, default=False)

        # Alias
        list_aliases = self._add_command('lib.alias.list', alias.list_)
        list_aliases.add_key('song', str)

        bind_alias = self._add_command('lib.alias.bind', alias.bind)
        bind_alias.add_key('song', str)
        bind_alias.add_key('aliases', IterType(str))

        unbind_alias = self._add_command('lib.alias.unbind', alias.unbind)
        unbind_alias.add_key('aliases', IterType(str))

        # Lyric
        set_lyric = self._add_command('lib.lyric.set', lyric.set_)
        set_lyric.add_key('song', str)
        set_lyric.add_key('path', str)

        show_lyric = self._add_command('lib.lyric.show', lyric.show)
        show_lyric.add_key('song', str)

        fetch_lyric = self._add_command('lib.lyric.fetch', lyric.fetch)
        fetch_lyric.add_key('songs', IterType(str))

        offset_lyric = self._add_command('lib.lyric.offset', lyric.offset)
        offset_lyric.add_key('song', str)
        offset_lyric.add_key('offset', int)

        # Playlist
        playlist_list = self._add_command('lib.playlist.list', playlist.list_)
        playlist_list.add_key('playlist', str, required=False)
        playlist_list.add_key('show_aliases', CONVERTER.boolean, required=False, default=False)
        playlist_list.add_key('show_playlists', CONVERTER.boolean, required=False, default=False)
        playlist_list.add_key('show_tech', CONVERTER.boolean, required=False, default=False)

        playlist_create = self._add_command('lib.playlist.create', playlist.create)
        playlist_create.add_key('name', str)

        playlist_add = self._add_command('lib.playlist.add', playlist.add)
        playlist_add.add_key('playlist', str)
        playlist_add.add_key('songs', IterType(str))

        playlist_kick = self._add_command('lib.playlist.kick', playlist.kick)
        playlist_kick.add_key('playlist', str)
        playlist_kick.add_key('songs', IterType(str))

        playlist_del = self._add_command('lib.playlist.del', playlist.del_)
        playlist_del.add_key('playlist', str)

        playlist_reorder = self._add_command('lib.playlist.reorder', playlist.reorder)
        playlist_reorder.add_key('playlist', str)
        playlist_reorder.add_key('song_ids', IterType(int))

        playlist_swap = self._add_command('lib.playlist.swap', playlist.swap)
        playlist_swap.add_key('playlist', str)
        playlist_swap.add_key('song1', str)
        playlist_swap.add_key('song2', str)

        playlist_move = self._add_command('lib.playlist.move', playlist.move)
        playlist_move.add_key('playlist', str)
        playlist_move.add_key('song', str)
        playlist_move.add_key('position', int)

        playlist_sort = self._add_command('lib.playlist.sort', playlist.sort)
        playlist_sort.add_key('playlist', str)
        playlist_sort.add_key('by_name', CONVERTER.boolean, required=False, default=False)
        playlist_sort.add_key('reverse', CONVERTER.boolean, required=False, default=False)

        # Config
        self._add_command('config.list', config.list_)

        config_show = self._add_command('config.show', config.show)
        config_show.add_key('option', str)

        config_set = self._add_command('config.set', config.set_)
        config_set.add_key('option', str)
        config_set.add_key('value', str)
        config_set.add_key('overwrite_corrupt', CONVERTER.boolean, required=False, default=False)

        config_unset = self._add_command('config.unset', config.unset)
        config_unset.add_key('option', str)

        self._add_command('config.open', config.open_)
        self._add_command('config.path', config.path)

    def _add_command(self, action: str, handler: Callable) -> Command:
        command = Command(action=action, handler=handler)
        self.commands[action] = command
        return command

    def process_request(self, request: dict) -> tuple[bool, tuple[dict, Callable] | Response]:
        result = {}
        if not isinstance(request, dict):
            return False, gen_response.Failed('request is not a dictionary')
        else:
            token = request.get('token', '')
            backend_token = CONFIG.backend_token
            if backend_token != '' and token != backend_token:
                return False, gen_response.AuthFailed()
            else:
                action = request.get('action', None)
                if action is None:
                    logger.error('Not \"action\" key found in request')
                    return False, gen_response.MissingKey('action')
        
                else:
                    command = self.commands.get(action, None)
                    if command is None:
                        logger.error(f'Invalid "action" value received: {action}')
                        return False, gen_response.UnknownAction(action)
                    else:
                        for key in command.keys:
                            value = request.get(key.name, None)
                            if value is None:
                                if key.required:
                                    return False, gen_response.MissingKey(key.name)
                                else:
                                    value = key.default
                            else:
                                try:
                                    value = key.converter(value)
                                except ValueError as e:
                                    return False, gen_response.InvalidKeyType(key.name, value, str(e))
                            
                            result[key.name] = value

                        for key in NON_ACTION_KEYS:
                            if key in request.keys():
                                result[key] = request[key]

                        unexpected_keys = set(request.keys()) - set(result.keys())
                        if len(unexpected_keys) > 0:
                            logger.warning(f'Unexpected key(s) received: {unexpected_keys}')

                        return True, (result, command.handler)
