import argparse
from pathlib import Path

from src.constants.cli import HELP_DESCRIPTION
from src.utils.text import strlen

class Builder:
    def _path(self, val):
        return str(Path(val).absolute())

    def _percent(self, val):
        try:
            val = int(val)
        except ValueError:
            raise argparse.ArgumentTypeError(f'{val} is not a valid percentage number')
        else:
            if val < 0 or val > 100:
                raise argparse.ArgumentTypeError(f'percentage must not be lower than 0 or higher than 100')
            else:
                return val

    def _add_parser(self, parser, action, *args, **kwargs):
        kwargs['parents'] = kwargs.get('parents', []) + [self.base]
        result = parser.add_parser(action, *args, **kwargs)
        result.set_defaults(**{parser.dest: action})
        return result

    def _get_description(self):
        description = ''
        lines = HELP_DESCRIPTION.splitlines()
        max_len = max(map(strlen, lines))
        separator = '=' * (max_len + 6)
        description += separator
        for line in lines:
            if len(line.strip()) > 0:
                description += f'\n   {line}'
            else:
                description += f'\n\n'
        description += f'\n\n{separator}'
        
        return description

    def build_parser(self):
        self.base = argparse.ArgumentParser(add_help=False)
        self.base.add_argument('--verbose', action='store_true', help='Print log to console')

        parser = argparse.ArgumentParser(
            prog='cascade',
            description=self._get_description(),
            formatter_class=argparse.RawDescriptionHelpFormatter
            )

        command_sub = parser.add_subparsers(dest='action', required=True)

        start_parser = self._add_parser(command_sub, 'start', help='Start CASCADE backend')
        start_parser.add_argument('-c', '--continue', action='store_true', help='Continue playing last song')
        start_parser.add_argument('--dev', action='store_true', help='Start in development mode')

        reboot_parser = self._add_parser(command_sub, 'reboot', help='Reboot CASCADE backend. Will fail if backend is not running')
        reboot_parser.add_argument('--dev', action='store_true', help='Reboot in development mode')
        reboot_parser.add_argument('-c', '--continue', action='store_true', help='Continue playing last song')

        dash_parser = self._add_parser(command_sub, 'dash', help='Open Dashboard')
        
        gui_parser = self._add_parser(command_sub, 'gui', help='Open GUI')

        status_parser = self._add_parser(command_sub, 'status', aliases=['st'], help='Show CASCADE status')
        status_parser.add_argument('-d', '--dev', action='store_true', help='Show dev info')

        open_epilog = 'You can open a song in library, a playlist or a file on disk, and you can specify it with the --type option.'
        open_parser = self._add_parser(command_sub, 'open', help='Open a song or playlist. Supports alias, file path and playlist name', epilog=open_epilog)
        open_parser.add_argument('song', type=str, help='Song to open')
        open_parser.add_argument('-t', '--type', type=str, help='Type of the song to open')

        play_all_parser = self._add_parser(command_sub, 'play-all', help='Play all songs in library')

        reload_parser = self._add_parser(command_sub, 'reload', help='Reload current songs')

        pause_parser = self._add_parser(command_sub, 'pause', help='Pause playing media')

        resume_parser = self._add_parser(command_sub, 'resume', help='Resume paused media')

        toggle_parser = self._add_parser(command_sub, 'toggle', help='Switch between playing and paused')

        stop_parser = self._add_parser(command_sub, 'stop', help='Stop playing')

        list_parser = self._add_parser(command_sub, 'list', help='Show current playlist')

        loop_parser = self._add_parser(command_sub, 'loop', help='Toggle loop mode')

        reverse = self._add_parser(command_sub, 'reverse', help='Toggle reverse playback mode')

        shuffle_parser = self._add_parser(command_sub, 'shuffle', help='Toggle shuffle mode')

        dice_parser = self._add_parser(command_sub, 'dice', help='Switch to a random song in current playlist')

        switch_parser = self._add_parser(command_sub, 'switch', help='Switch to a song in current playlist via number')
        switch_parser.add_argument('number', type=int, help='Number in playlist of song to switch. Negative number means count from the last')

        prev_parser = self._add_parser(command_sub, 'prev', aliases=['previous'], help='Switch to the previous song in current playlist')

        next_parser = self._add_parser(command_sub, 'next', help='Switch to the next song in current playlist')

        seek_parser = self._add_parser(command_sub, 'seek', help='Jump to a specific time')
        seek_parser.add_argument('time', help='Time to jump to (HH:MM:SS)')

        jump_parser = self._add_parser(command_sub, 'jump', help='Jump to progress of the current song')
        jump_parser.add_argument('progress', type=self._percent, help='Progress to jump to (percentage)')

        replay_parser = self._add_parser(command_sub, 'replay', help='Clear memorized progress and jump to the beginning of the current playing song')

        volume_parser = self._add_parser(command_sub, 'volume', help='Set volume')
        volume_parser.add_argument('volume', type=str, help='Volume to set (percentage)')

        mute_parser = self._add_parser(command_sub, 'mute', help='Toggle mute')

        lyric_parser = self._add_parser(command_sub, 'lyric', help='Switch between lyric sources [local/online]')

        lib_parser = self._add_parser(command_sub, 'lib', aliases=['library'], help='Manage library')

        lib_sub = lib_parser.add_subparsers(dest='lib_action', required=True)

        lib_info_parser = self._add_parser(lib_sub, 'info', help='Show information of a song')
        lib_info_parser.add_argument('songs', type=str, nargs='+', help='Song to show')
        lib_info_parser.add_argument('-a', '--show-aliases', action='store_true', help='Show aliases of the song')
        lib_info_parser.add_argument('-p', '--show-playlists', action='store_true', help='Show playlists the song is in')

        lib_list_parser = self._add_parser(lib_sub, 'list', help='Show all songs in library')
        lib_list_parser.add_argument('-a', '--show-aliases', action='store_true', help='Show aliases of songs')
        lib_list_parser.add_argument('-p', '--show-playlists', action='store_true', help='Show playlists each song is in')
        lib_list_parser.add_argument('-t', '--show-tech', action='store_true', help='Show technical information')

        lib_search_parser = self._add_parser(lib_sub, 'search', help='Search for songs in library')
        lib_search_parser.add_argument('keyword', type=str, nargs='+', help='Keyword to search')
        lib_search_parser.add_argument('-o', '--or', action='store_true', help='Get all results that match any one the keywords')

        lib_add_parser = self._add_parser(lib_sub, 'add', help='Add songs to library')
        lib_add_parser.add_argument('paths', type=self._path, nargs='+', help='Path of songs to add')
        lib_add_parser.add_argument('-a', '--aliases', type=str, nargs='+', default=[], help='Aliases to bind to the new songs')
        lib_add_parser.add_argument('--skip-meta', action='store_true', help='Disable automatic setting metadata')
        lib_add_parser.add_argument('--skip-alias', action='store_true', help='Disable automatic binding aliases')
        lib_add_parser.add_argument('--skip-lyric', action='store_true', help='Disable automatic setting lyric file')
        lib_add_parser.add_argument('--loose-path', action='store_true', help='Adding songs without checking the availability of the paths. May cause automatic setting of metadata and binding of aliases to fail')

        lib_del_parser = self._add_parser(lib_sub, 'del', help='Delete songs from library')
        lib_del_parser.add_argument('songs', type=str, nargs='+', help='Songs to delete')

        lib_prune_parser = self._add_parser(lib_sub, 'prune', help='Delete all songs which file no longer exists')
        lib_prune_parser.add_argument('-d', '--dry-run', action='store_true', help='Show found files without deleting')

        lib_scan_parser = self._add_parser(lib_sub, 'scan', help='Scan a directory for all supported audio files and add them to library')
        lib_scan_parser.add_argument('dir', type=self._path, help='directory to scan')
        lib_scan_parser.add_argument('--playlist', type=str, default=None, help='Playlist to add all found songs to')
        lib_scan_parser.add_argument('-r', '--recurse', action='store_true', help='Enable recursive scanning')
        lib_scan_parser.add_argument('-d', '--dry-run', action='store_true', help='Show found files without adding to library')
        lib_scan_parser.add_argument('--skip-meta', action='store_true', help='Disable automatic setting metadata')
        lib_scan_parser.add_argument('--skip-alias', action='store_true', help='Disable automatic binding alias')
        lib_scan_parser.add_argument('--skip-lyric', action='store_true', help='Disable automatic setting lyric file')

        lib_reset_parser = self._add_parser(lib_sub, 'reset', help='Reset library and delete all data')
        lib_reset_parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation')

        meta_epilog = '\n'.join(('Supported metadata:',
                                '  name: The name of the song. Can not be used to reference the song like alias',
                                '  artist: The artist of the song',
                                '  album: The album of the song'))
        meta_parser = self._add_parser(lib_sub, 'meta', aliases=['metadata'], help='Manage metadata of songs in library', epilog=meta_epilog)
        meta_sub = meta_parser.add_subparsers(dest='meta_action', required=True)

        meta_set_parser = self._add_parser(meta_sub, 'set', help='Set the value of metadata of a song in library')
        meta_set_parser.add_argument('song', type=str, help='Song to set metadata')
        meta_set_parser.add_argument('--name', type=str, default=None, help='Name of the song')
        meta_set_parser.add_argument('--artist', type=str, default=None, help='Artist of the song')
        meta_set_parser.add_argument('--album', type=str, default=None, help='Album of the song')

        meta_read_file_parser = self._add_parser(meta_sub, 'read-file', help='Set the value of metadata of a song in library with values read from file')
        meta_read_file_parser.add_argument('song', type=str, help='Song to set metadata')
        meta_read_file_parser.add_argument('--name', action='store_true', help='Set name of the song')
        meta_read_file_parser.add_argument('--artist', action='store_true', help='Set artist of the song')
        meta_read_file_parser.add_argument('--album', action='store_true', help='Set album of the song')
        meta_read_file_parser.add_argument('--all', action='store_true', help='Set all available metadata')

        alias_parser = self._add_parser(lib_sub, 'alias', help='Manage aliases of songs in library')
        alias_sub = alias_parser.add_subparsers(dest='alias_action', required=True)

        alias_list_parser = self._add_parser(alias_sub, 'list', help='Show all bound aliases of a song in library')
        alias_list_parser.add_argument('song', type=str, help='Song to list aliases')

        alias_bind_parser = self._add_parser(alias_sub, 'bind', help='Bind aliases to a song in library')
        alias_bind_parser.add_argument('song', type=str, help='Song to bind aliases to')
        alias_bind_parser.add_argument('aliases', type=str, nargs='+', help='aliases to bind to song')

        alias_unbind_parser = self._add_parser(alias_sub, 'unbind', help='Unbind aliases from their songs in library')
        alias_unbind_parser.add_argument('aliases', type=str, nargs='+', help='Aliases to unbind')

        lyric_parser = self._add_parser(lib_sub, 'lyric', help='Manage lyrics')
        lyric_sub = lyric_parser.add_subparsers(dest='lyric_action', required=True)

        lyric_set_parser = self._add_parser(lyric_sub, 'set', help='Set lyric file of a song. Using empty string (\"\") to unset')
        lyric_set_parser.add_argument('song', type=str, help='Song to set lyric file')
        lyric_set_parser.add_argument('path', type=self._path, help='Path of lyric file')

        lyric_show_parser = self._add_parser(lyric_sub, 'show', help='Show lyric of a song')
        lyric_show_parser.add_argument('song', type=str, help='Song to show lyric')

        lyric_fetch_parser = self._add_parser(lyric_sub, 'fetch', help='Fetch lyric of songs from online sources')
        lyric_fetch_parser.add_argument('songs', type=str, nargs='+', help='Songs to fetch lyric')

        lyric_offset_parser = self._add_parser(lyric_sub, 'offset', help='Set lyric offset of song')
        lyric_offset_parser.add_argument('song', type=str, help='Song to set offset')
        lyric_offset_parser.add_argument('offset', type=int, help='Offset to set (ms)')


        playlist_parser = self._add_parser(lib_sub, 'playlist', aliases=['pl'], help='Manage playlists')
        playlist_sub = playlist_parser.add_subparsers(dest='playlist_action', required=True)

        playlist_list_parser = self._add_parser(playlist_sub, 'list', help='Show all songs in a playlist. Show names of all playlists in library if no playlists are provided')
        playlist_list_parser.add_argument('playlist', type=str, nargs='?', default=None, help='Name of playlist to list')
        playlist_list_parser.add_argument('-a', '--show-aliases', action='store_true', help='Show aliases of songs')
        playlist_list_parser.add_argument('-p', '--show-playlists', action='store_true', help='Show playlists each song is in')
        playlist_list_parser.add_argument('-t', '--show-tech', action='store_true', help='Show technical information')
        
        playlist_create_parser = self._add_parser(playlist_sub, 'create', help='Create a new playlist')
        playlist_create_parser.add_argument('name', type=str, help='Name of playlist to create')

        playlist_add_parser = self._add_parser(playlist_sub, 'add', help='Add songs in library to a playlist')
        playlist_add_parser.add_argument('playlist', type=str, help='Playlist to add song to')
        playlist_add_parser.add_argument('songs', type=str, nargs='+', help='Songs to add to playlist')

        playlist_kick_parser = self._add_parser(playlist_sub, 'kick', help='Remove songs from a playlist')
        playlist_kick_parser.add_argument('playlist', type=str, help='Playlist to remove song from')
        playlist_kick_parser.add_argument('songs', type=str, nargs='+', help='Songs to remove from playlist')

        playlist_del_parser = self._add_parser(playlist_sub, 'del', help='Delete a playlist')
        playlist_del_parser.add_argument('playlist', type=str, help='Playlist to delete')

        config_parser = self._add_parser(command_sub, 'config', aliases=['configure'], help='Manage configuration')
        config_sub = config_parser.add_subparsers(dest='config_action', required=True)
        config_parent = argparse.ArgumentParser(add_help=False)
        config_parent.add_argument(
            '-d', '--direct', 
            action=argparse.BooleanOptionalAction, 
            default=None,
            help='Bypass CASCADE backend and operate on local configure file directly'
            )

        config_list_parser = self._add_parser(config_sub, 'list', parents=[config_parent], help='Show information all options')

        config_show_parser = self._add_parser(config_sub, 'show', parents=[config_parent], help='Show information of an option')
        config_show_parser.add_argument('option', type=str, help='Option to show')

        config_set_parser = self._add_parser(config_sub, 'set', parents=[config_parent], help='Set value of an option. You might need to reboot CASCADE backend to make some options take effect')
        config_set_parser.add_argument('option', type=str, help='Option to set')
        config_set_parser.add_argument('value', type=str, help='Value to set')
        config_set_parser.add_argument('--overwrite-corrupt', action='store_true', help='Overwrite corrupted configure file.')

        config_unset_parser = self._add_parser(config_sub, 'unset', parents=[config_parent], help='Remove the setting of an option from configure file and fallback to default value')
        config_unset_parser.add_argument('option', type=str, help='Option to unset')
        
        config_gui_parser = self._add_parser(config_sub, 'gui', parents=[config_parent], help='Open configure GUI')

        config_open_parser = self._add_parser(config_sub, 'open', parents=[config_parent], help='Open configure file with system\'s default application')

        config_path_parser = self._add_parser(config_sub, 'path', parents=[config_parent], help='Show path of configure file')

        exit_parser = self._add_parser(command_sub, 'exit', aliases=['quit'], help='Exit CASCADE backend')

        kill_parser = self._add_parser(command_sub, 'kill', help='Kill all CASCADE backend processes. May cause unpredictable error')

        return parser