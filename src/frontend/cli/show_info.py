import sys
from datetime import datetime

import readchar

from src.config import CONFIG
from .song_output import SongOutput
from src.utils.tui import box
from src.utils.escape_code import ESCAPE_CODE as EC

def cli_box(*args, **kwargs) -> str:
    return box(*args, style=CONFIG.cli_box_style, **kwargs)

def show_notifies(notifies: list[list[float, str]] | None = None):
    if notifies is None:
        notifies = []

    if len(notifies) > 0:
        lines = [
            f'{EC.white}Notifies from CASCADE backend ({len(notifies)}):{EC.reset}',
            ''
        ]
        for notify in notifies:
            time_ = datetime.fromtimestamp(round(notify[0]))
            lines.append(f'{EC.cyan}{EC.bold}{time_}{EC.reset}    {notify[1]}')
        print(cli_box('\n'.join(lines)))

def show_option_info(info: dict):
    name = info.get('name', 'N/A')
    type_ = info.get('type', 'N/A')
    value = info.get('value', 'N/A')
    source = info.get('source', 'N/A')
    default = info.get('default', 'N/A')
    description = info.get('description', 'No Description')
    
    lines = [
        f'{EC.blue}Name:{EC.reset} {name}',
        f'{EC.blue}Type:{EC.reset} {type_}',
        f'{EC.blue}Value:{EC.reset} {value}',
        f'{EC.blue}Source:{EC.reset} {source}',
        f'{EC.blue}Default Value:{EC.reset} {default}',
        f'\n{EC.white}\"{EC.italics}{description}\"{EC.reset}'
        ]
    print(cli_box('\n'.join(lines)))

def show_song_info(
        info: list[dict] | dict,
        empty_msg: str = 'No information to be shown',
        short: bool = False,
        full: bool = False,
        show_aliases: bool = False,
        show_playlists: bool = False,
        show_num: bool = False,
        show_tech: bool = False,
        ):
    if not isinstance(info, (list, tuple)):
        info = (info,)
    if len(info) > 0:
        print()
        for i, song in enumerate(info):
            output = SongOutput(song)

            if short:
                line = f'{EC.cyan}ID {output.lib_id}{EC.reset} {EC.dim}-{EC.reset} {EC.blue}{output.display_name}{EC.reset}'
                if show_num:
                    line = f'{EC.italics}{EC.blue}{i+1:02g}.{EC.reset} {line}'
                print(line)
            else:
                if show_num:
                    lines = [f'{EC.bold}{i+1}. {EC.white}{output.display_name}{EC.reset}']
                else:
                    lines = [f'{EC.bold}{EC.white}{output.display_name}{EC.reset}']

                lines += [
                    f'\n{EC.blue}Name:{EC.reset} {output.name}',
                    f'{EC.blue}Artist:{EC.reset} {output.artist}',
                    f'{EC.blue}Album:{EC.reset} {output.album}',
                    f'\n{EC.blue}Duration:{EC.reset} {output.duration}',
                ]

                if show_tech:
                    lines += [
                        f'\n{EC.yellow}Bitrate:{EC.reset} {output.bitrate} kbps',
                        f'{EC.yellow}Sample Rate:{EC.reset} {output.sample_rate}',
                        f'{EC.yellow}Channels:{EC.reset} {output.channels}',
                    ]

                lines += [
                    f'\n{EC.blue}Path:{EC.reset} {output.path}',
                    f'{EC.blue}Lyric Path:{EC.reset} {output.lyric}',
                    f'{EC.blue}Lyric Offset:{EC.reset} {output.lyric_offset}',
                    f'\n{EC.blue}Library ID:{EC.reset} {output.lib_id}'
                ]

                if show_aliases:
                    lines += [f"\n{EC.yellow}Aliases ({output.aliases_num}):{EC.reset} {output.aliases}"]

                if show_playlists:
                    lines += [f"\n{EC.yellow}Playlists ({output.playlists_num}):{EC.reset} {output.playlists}"]

                print(cli_box('\n'.join(lines)))

                if not full and sys.stdin.isatty():
                    key = None
                    print(
                        f'\n  {EC.white}{len(info)-i-1} left{EC.reset}      {EC.green}Enter - Next{EC.reset}        {EC.red}q - Quit{EC.reset}',
                        end='',
                        flush=True
                        )
                    while key != readchar.key.ENTER:
                        try:
                            key = readchar.readkey()
                            if key == 'q':
                                break
                        except KeyboardInterrupt:
                            break
                    else:
                        print('\033[1A\r\033[J')
                        continue

                    print('\033[1A\r\033[J')
                    return
                    

    else:
        print(f'{EC.red}{empty_msg}{EC.reset}')
