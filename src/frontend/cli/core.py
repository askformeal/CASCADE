import sys
from pathlib import Path
import readchar
import json

from src.log import setup_logger
from src.sentinels import SENTINELS
from src.frontend.client import send_request
from src.process import ProcessManager
from src.constants.paths import CLI_LOG_PATH
from src.constants.frontend import ATTACHMENT_REQUIRED_ACTIONS
from src.constants.cli import FAIL_TAG, OK_TAG
from src.config_manager import CONFIG_MANAGER
from src.frontend.song_output import SongOutput
from src.utils.escape_code import ESCAPE_CODE as EC
from src.utils.time_ import format_time
from .build_parser import Builder
from .process import process_request
from .show_info import (
    cli_box,
    show_notifies,
    show_option_info,
    show_song_info
    )

def main():
    parser = Builder().build_parser()
    args = vars(parser.parse_args())
    args = process_request(args)


    logger = setup_logger(
        __name__, 
        CLI_LOG_PATH, 
        add_console=args['verbose']
        )
    logger.debug(f'Arguments ready: {args}')
    
    process = ProcessManager(logger)
    
    environ = {
        'CASCADE_DEV': int(args.get('dev', 0)), 
        'CASCADE_CONTINUE': int(args.get('continue', 0))
    }

    if args['action'] == 'start':
        _start_backend(process, **environ)
        show_notifies(get_notifies())

    elif args['action'] == 'reboot':
        _reboot_backend(process, **environ)
        show_notifies(get_notifies())

    elif args['action'] == 'kill':
        print(f'Killing CASCADE backend processes...')
        result = process.kill()
        for pid, process_result in result:
            msg = {
                SENTINELS.PERMISSION_INSUFFICIENT: f'{FAIL_TAG} Access Denied',
                SENTINELS.INVALID_PID: f'{FAIL_TAG} PID Invalid',
                SENTINELS.PROCESS_NOT_FOUND: f'{FAIL_TAG} Process Not Exist',
                SENTINELS.GRACE_KILL: f'{OK_TAG} Gracefully Terminated',
                SENTINELS.FORCE_KILL: f'{OK_TAG} Forcefully Killed'
            }[process_result]

            print(f' PID {pid}: {msg}')

    elif args['action'] == 'dash':
        from src.frontend.dash.core import Dash
        Dash().run()
    
    elif args['action'] == 'gui':
        from src.frontend.gui.core import GUI
        GUI().run()

    elif args['action'] == 'config.gui':
        from src.frontend.config_gui.core import ConfigGUI
        ConfigGUI(args['direct']).run()

    else:
        if 'direct' in args.keys() and args['direct'] is None:
            args['direct'] = False

        if args['action'] == 'lib.reset':
            answer = ''
            while not args['yes'] and answer not in ('y', 'n'):
                print('This action will reset the database and all data including songs and playlists will be permanently lost. Continue? [Y/N]', end='', flush=True)
                answer = readchar.readkey().lower()
                print()
            if answer == 'n':
                print('Cancelled')
                return
            del args['yes']

# -------------------------------------- Pre-response --------------------------------------

        if args['action'].startswith('config.') and args.get('direct', False):
            if args['action'] == 'config.list':
                response = CONFIG_MANAGER.get_all_option_info()
            elif args['action'] == 'config.show':
                response = CONFIG_MANAGER.get_option_info(args['option'])
            elif args['action'] == 'config.set':
                response = CONFIG_MANAGER.set_option_value(args['option'], args['value'], args['overwrite_corrupt'])
            elif args['action'] == 'config.unset':
                response = CONFIG_MANAGER.unset_option(args['option'])
            elif args['action'] == 'config.open':
                response = CONFIG_MANAGER.open_config_file()
            elif args['action'] == 'config.path':
                response = CONFIG_MANAGER.get_path()
            logger.info(f'Getting response from local config manager...')
            response = dict(response)
        else:
            if 'direct' in args.keys():
                del args['direct']
            request = _wrap_request(args)
            logger.info(f'Sending request to backend...\n{json.dumps(request, indent=4)}')
            response = send_request(**request)

# -------------------------------------- Post-response --------------------------------------

        logger.info(f'Response received: {json.dumps(response, indent=4)}')

        action = args['action']
        code =  response.get('code', None)
        msg = response.get('msg', None)
        attachment = response.get('attachment', None)
        failed = response.get('failed', [])
        notifies = response.get('notifies', [])

        show_notifies(notifies)

        if code is None or msg is None:
            print(f'{FAIL_TAG} Invalid response received from CASCADE backend')

        elif code == 0:
            print(cli_box(f'{OK_TAG} {response['msg']}'))
            if action == 'lib.add' and isinstance(attachment, list):
                for add_response in attachment:
                    print(add_response['msg'])

            elif action in ATTACHMENT_REQUIRED_ACTIONS:
                if attachment is None and not (action == 'lib.scan' and not args['dry_run']):
                    print(f'{FAIL_TAG} action {action} was expecting an attachment but none was received from CASCADE backend')
                else:
                    # these actions will be expecting an attachment
                    if action == 'status':
                        
                        output = SongOutput(attachment)

                        if output.playing_all:
                            playlist = '[ Playing all songs in library ]'
                        else:
                            playlist = f'Playlist: {output.playlist_name}'

                        text = '\n'.join((
                                        f'\n{output.display_name} - {output.artist} [{output.current_num} / {output.playlist_len}]',
                                        f'[{output.time} / {output.length}] {output.percentage}%\n',
                                        f'In library: {output.in_lib}',
                                        f'Album: {output.album}',
                                        '',
                                        playlist,
                                        '',
                                        f'Path: {output.path}',
                                        f'Lyric File Path: {output.lyric}',
                                        '',
                                        f'Player status: {output.player_status}',
                                        f'Volume: {output.volume}%',
                                        f'Mute: {output.mute}',
                                        '',
                                        f'Shuffle: {output.shuffle}',
                                        f'Loop: {output.loop}',
                                        f'Reverse: {output.reverse}',
                                        f'Online Lyric: {output.online_lyric}',
                                        '',
                                        f'Audio Engine: {output.engine}',
                                        '',
                                        f'CASCADE backend has been running for {output.run_time}',
                        ))

                        if output.dev:
                            text += '\n\nDEVELOPMENT MODE ON'

                        print(cli_box(text))

                    elif action == 'list':
                        show_song_info(attachment, 'No songs are being played', show_num=True)

                    elif action == 'lib.info':
                        show_song_info(attachment, 
                                        show_tech=True, 
                                        show_aliases=args['show_aliases'],
                                        show_playlists=args['show_playlists'])

                    elif action == 'lib.list':
                        show_song_info(attachment, 
                                        'No songs in library', 
                                        show_tech=args['show_tech'],
                                        show_aliases=args['show_aliases'], 
                                        show_playlists=args['show_playlists'])

                    elif action == 'lib.search':
                        show_song_info(attachment, 'No results to be shown')

                    elif action == 'lib.prune':
                        show_song_info(attachment, 'No songs to be shown')

                    elif action == 'lib.scan' and args['dry_run']:
                        if len(attachment) > 0:
                            print('-'*50)
                            for path in attachment:
                                print(path)
                        else:
                            print('No files to be shown')

                    elif action == 'lib.alias.list':
                        if len(attachment) > 0:
                            print('Alias(es):')
                            print(f'  {"\n  ".join(attachment)}')
                        else:
                            print('No aliases are bound to this song')

                    elif action == 'lib.lyric.show':
                        lines = [f"Path: {attachment.get('path', '?')}", '']
                        for timestamp, text in attachment.get('lyric', []):
                            lines.append(f"[{format_time(timestamp)}] {text.strip().replace('\n', ' \\ ')}")

                        print(cli_box('\n'.join(lines)))

                    elif action == 'lib.playlist.list':
                        if args['playlist'] is not None:
                            show_song_info(attachment, 
                                            'Playlist empty',
                                            show_tech=args['show_tech'],
                                            show_aliases=args['show_aliases'],
                                            show_playlists=args['show_playlists'])
                        else:
                            if len(attachment) > 0:
                                print(f'Found {len(attachment)} playlist(s) in library:')
                                for playlist in attachment:
                                    print(f'  {playlist['name']}')
                            else:
                                print('No playlists in library')
                    elif action == 'config.list':
                        for option_info in attachment:
                            show_option_info(option_info)

                    elif action == 'config.show':
                        show_option_info(attachment)

                    elif action == 'config.path':
                        print(cli_box(attachment))

        elif code == 1:
            print(cli_box(f'{FAIL_TAG} {response['msg']}'))

        elif code == 2:
            print(cli_box(f'{FAIL_TAG} failed to connect to CASCADE backend. You can try to use the start subcommand to start it'))

        elif code == 3:
            print(cli_box(f'{FAIL_TAG} received an unexpected default response code from CASCADE backend which is not to be used under any circumstances. Please report this error'))

        elif code == 4:
            print(cli_box(f'{FAIL_TAG} CASCADE backend is exiting'))

        elif code == 5:
            print(cli_box(f'{FAIL_TAG} Token rejected, authorization failed'))

        else:
            print(cli_box(f'{FAIL_TAG} Unknown response code \"{code}\"'))

        if len(failed) > 0:
            lines = [f'{EC.red}There are failed actions ({len(failed)}):{EC.rs}\n']
            lines += list(map(lambda x: f'  {x['msg']}', failed))
            print(cli_box('\n'.join(lines)))

        logger.info(f'Exit with code {code}')
        print()
        return code

def _wrap_request(args):
    args['source'] = 'cli'
    args['cwd'] = str(Path.cwd())
    args['notify_support'] = True
    return args

def get_notifies():
    return send_request(**_wrap_request({'action':'get_notifies'})).get('notifies', [])

def _start_backend(process, **kwargs):
    print(f'Starting backend...')
    for name, value in kwargs.items():
        print(f'  {EC.dim}{name}={value}{EC.reset}')
    print()
    result = process.start(**kwargs)
    if result is SENTINELS.SUCCESS:
        print(f'{OK_TAG} CASCADE backend is now up and running')
    elif result is SENTINELS.BACKEND_ALREADY_RUNNING:
        print(f'{FAIL_TAG} CASCADE backend is already running')
    elif result is SENTINELS.FAILED_START_BACKEND:
        print(f'{FAIL_TAG} Failed to start CASCADE backend. Examine log files for more information')
    return result

def _reboot_backend(process, **kwargs):
    print(f'Rebooting backend...')
    for name, value in kwargs.items():
        print(f'  {EC.dim}{name}={value}{EC.reset}')
    print()
    result = process.reboot(**kwargs)
    if result is SENTINELS.SUCCESS:
        print(f'{OK_TAG} CASCADE backend is successfully rebooted')
    elif result is SENTINELS.BACKEND_NOT_RUNNING:
        print(f'{FAIL_TAG} CASCADE backend is not running')
    elif result is SENTINELS.FAILED_EXIT_BACKEND:
        print(f'{FAIL_TAG} Failed to exit backend')
    elif result is SENTINELS.FAILED_START_BACKEND:
        print(f'{FAIL_TAG} Backend is exited but failed to start. Examine log files for more information')


if __name__ == '__main__':
    sys.exit(main())