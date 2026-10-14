from datetime import datetime
import sys
from pathlib import Path
import readchar
import json

from src.log import setup_logger
from src.sentinels import SENTINELS, Sentinel
from src.frontend.client import send_request
from src.process import ProcessManager
from src.constants.paths.log import CLI_LOG
from src.constants.frontend import ATTACHMENT_REQUIRED_ACTIONS
from src.constants.cli import FAIL_TAG, OK_TAG, NON_REQUEST_KEYS
from src.config_manager import CONFIG_MANAGER
from .song_output import SongOutput
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

def main() -> int:
    parser = Builder().build_parser()
    args = vars(parser.parse_args())
    args = process_request(args)

    logger = setup_logger(
        __name__, 
        CLI_LOG, 
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
        print_short = args.get('short', False)
        print_full = args.get('full', False)

        if args['action'] == 'status' and args['dev']:
            dev_status = True
        else:
            dev_status = False

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
            args = _filter_args(args)
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
            print(cli_box(f'\n{FAIL_TAG} Invalid response received from CASCADE backend\n\n'))

        elif code == 0:
            print(cli_box(f'\n{OK_TAG} {response['msg']}\n\n'))
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
                            playlist = f'{EC.yellow}[ Playing all songs in library ]{EC.reset}'
                        else:
                            playlist = f'{EC.blue}Playlist:{EC.reset} {output.playlist_name}'

                        text = (
                            f'{EC.bold}{EC.white}{output.display_name} - {output.artist}{EC.reset} [{output.current_num} / {output.playlist_len}]',
                            '',
                            f'[{EC.yellow}{output.time}{EC.reset} / {EC.yellow}{output.length}{EC.reset}] {output.percentage}%',
                            '',
                            f'{EC.blue}In library:{EC.reset} {output.in_lib}',
                            f'{EC.blue}Album:{EC.reset} {output.album}',
                            '',
                            playlist,
                            '',
                            f'{EC.blue}Path:{EC.reset} {output.path}',
                            f'{EC.blue}Lyric File Path:{EC.reset} {output.lyric}',
                            '',
                            f'{EC.blue}Player status:{EC.reset} {output.player_status}',
                            f'{EC.blue}Volume:{EC.reset} {output.volume}%',
                            f'{EC.blue}Mute:{EC.reset} {output.mute}',
                            '',
                            f'{EC.blue}Shuffle:{EC.reset} {output.shuffle}',
                            f'{EC.blue}Loop:{EC.reset} {output.loop}',
                            f'{EC.blue}Reverse:{EC.reset} {output.reverse}',
                            f'{EC.blue}Online Lyric:{EC.reset} {output.online_lyric}',
                            '',
                            f'{EC.blue}Audio Engine:{EC.reset} {output.engine}',
                            
                        )

                        if dev_status:
                            text += (
                                '',
                                '',
                                f'{EC.bold}{EC.white}Development information{EC.reset}',
                                '',
                                f'{EC.blue}Backend run time:{EC.reset} {output.run_time}',
                                '',
                                f'{EC.blue}Request rate:{EC.reset} {output.request_rate}'
                            )

                        if output.dev:
                            text += (
                                '',
                                '',
                                f'{EC.cyan}DEVELOPMENT MODE ON{EC.reset}'
                                )
                        text = '\n'.join(text)

                        print(cli_box(text))

                    elif action == 'task':
                        lines = []
                        if len(attachment) > 0:
                            lines += [
                                f'{EC.white}{len(attachment)} tasks{EC.reset}',
                                ''
                                ]
                            
                            for i, task in enumerate(attachment):
                                if task['status'] == 'running':
                                    status = f'{EC.yellow}RUNNING{EC.reset}'
                                elif task['status'] == 'succeed':
                                    status = f'{EC.green}SUCCEED{EC.reset}'
                                elif task['status'] == 'failed':
                                    status = f'{EC.red}FAILED{EC.reset}'
                                else:
                                    status = f'{EC.white}{task['status']}{EC.reset}'

                                if task['max_progress'] > 0:
                                    progress = f"[{task['progress']}/{task['max_progress']}] "
                                else:
                                    progress = ''
                                lines.append(f'{EC.cyan}{i+1}.{EC.reset} {EC.white}{task['name']}{EC.cyan} {progress}{status}')
                                for record in task['logs']:
                                    time_ = datetime.fromtimestamp(round(record[0]))
                                    lines.append(f'  {EC.cyan}{time_}{EC.reset}    {record[1]}')
                                lines.append('')
                        else:
                            lines = [f'{EC.red}No tasks{EC.reset}']

                        print(cli_box('\n'.join(lines)))

                    elif action == 'list':
                        show_song_info(
                            attachment,
                            'No songs are being played',
                            short=print_short,
                            full=print_full,
                            show_num=True
                            )

                    elif action == 'lib.info':
                        show_song_info(
                            attachment,
                            short=print_short,
                            full=print_full,
                            show_tech=True, 
                            show_aliases=args['show_aliases'],
                            show_playlists=args['show_playlists']
                            )

                    elif action == 'lib.list':
                        show_song_info(
                            attachment, 
                            'No songs in library',
                            short=print_short,
                            full=print_full,
                            show_tech=args['show_tech'],
                            show_aliases=args['show_aliases'], 
                            show_playlists=args['show_playlists'])

                    elif action == 'lib.search':
                        show_song_info(
                            attachment,
                            'No results to be shown',
                            short=print_short,
                            full=print_full
                            )

                    elif action == 'lib.prune':
                        show_song_info(
                            attachment,
                            'No songs to be shown',
                            short=print_short,
                            full=print_full
                            )

                    elif action == 'lib.scan' and args['dry_run']:
                        if len(attachment) > 0:
                            for path in attachment:
                                print(path)
                        else:
                            print(f'{EC.red}No files to be shown{EC.reset}')

                    elif action == 'lib.alias.list':
                        if len(attachment) > 0:
                            print(f'{EC.blue}Alias(es):{EC.reset}')
                            print(f'  {"\n  ".join(attachment)}')
                        else:
                            print(f'{EC.red}No aliases are bound to this song{EC.reset}')

                    elif action == 'lib.lyric.show':
                        lines = [f"{EC.blue}Path:{EC.reset} {attachment.get('path', '?')}", '']
                        for timestamp, text in attachment.get('lyric', []):
                            lines.append(f"[{format_time(timestamp)}] {text.strip().replace('\n', ' \\ ')}")

                        print(cli_box('\n'.join(lines)))

                    elif action == 'lib.playlist.list':
                        if args['playlist'] is not None:
                            show_song_info(attachment, 
                                            'Playlist empty',
                                            short=print_short,
                                            full=print_full,
                                            show_tech=args['show_tech'],
                                            show_aliases=args['show_aliases'],
                                            show_playlists=args['show_playlists'])
                        else:
                            if len(attachment) > 0:
                                print(f'{EC.white}Found {len(attachment)} playlist(s) in library:{EC.reset}')
                                for playlist in attachment:
                                    print(f'  {playlist['name']}')
                            else:
                                print(f'{EC.red}No playlists in library{EC.reset}')
                    elif action == 'config.list':
                        for option_info in attachment:
                            show_option_info(option_info)

                    elif action == 'config.show':
                        show_option_info(attachment)

                    elif action == 'config.path':
                        print(cli_box(attachment))

        elif code == 1:
            print(cli_box(f'\n{FAIL_TAG} {response['msg']}\n\n'))

        elif code == 2:
            print(cli_box(f'\n{FAIL_TAG} failed to connect to CASCADE backend. You can try to use the start subcommand to start it\n\n'))

        elif code == 3:
            print(cli_box(f'\n{FAIL_TAG} received an unexpected default response code from CASCADE backend which is not to be used under any circumstances. Please report this error\n\n'))

        elif code == 4:
            print(cli_box(f'\n{FAIL_TAG} CASCADE backend is exiting\n\n'))

        elif code == 5:
            print(cli_box(f'\n{FAIL_TAG} Token rejected, authorization failed\n\n'))

        else:
            print(cli_box(f'\n{FAIL_TAG} Unknown response code \"{code}\"\n\n'))

        if len(failed) > 0:
            lines = [f'{EC.red}There are failed actions ({len(failed)}):{EC.rs}\n']
            lines += list(map(lambda x: f'  {x['msg']}', failed))
            print(cli_box('\n'.join(lines)))

        logger.info(f'Exit with code {code}')
        print()
        return code

def _wrap_request(args: dict) -> dict:
    args['source'] = 'cli'
    args['cwd'] = str(Path.cwd())
    args['notify_support'] = True
    return args

def get_notifies() -> list[list[float | str]]:
    return send_request(**_wrap_request({'action':'get_notifies'})).get('notifies', [])

def _start_backend(process: ProcessManager, **kwargs) -> Sentinel:
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

def _reboot_backend(process: ProcessManager, **kwargs) -> Sentinel:
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

def _filter_args(args: dict) -> dict:
    for key in NON_REQUEST_KEYS:
        if key in args.keys():
            del args[key]

    return args


if __name__ == '__main__':
    sys.exit(main())