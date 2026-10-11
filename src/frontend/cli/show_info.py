from src.config import CONFIG
from .song_output import SongOutput
from src.utils.tui import box
from src.utils.escape_code import ESCAPE_CODE as EC

def cli_box(*args, **kwargs) -> str:
    return box(*args, style=CONFIG.cli_box_style, **kwargs)

def show_notifies(notifies: list[str] | None = None):
    if notifies is None:
        notifies = []

    if len(notifies) > 0:
        lines = [
            f'Notifies from CASCADE backend ({len(notifies)}):'
        ]
        lines += list(map(lambda x: f'  {x}', notifies))
        print(cli_box('\n'.join(lines)))

def show_option_info(info: dict):
    name = info.get('name', 'N/A')
    type_ = info.get('type', 'N/A')
    value = info.get('value', 'N/A')
    source = info.get('source', 'N/A')
    default = info.get('default', 'N/A')
    description = info.get('description', 'No Description')
    
    lines = [
        f'Name: {name}',
        f'Type: {type_}',
        f'Value: {value}',
        f'Source: {source}',
        f'Default Value: {default}',
        f'\n\"{description}\"'
        ]
    print(cli_box('\n'.join(lines)))

def show_song_info(
        info: list[dict] | dict,
        empty_msg: str = 'No information to be shown',
        short: bool = False,
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
                    lines = [f'{i+1}. {output.display_name}']
                else:
                    lines = [f'{output.display_name}']

                lines += [
                    f'\nName: {output.name}',
                    f'Artist: {output.artist}',
                    f'Album: {output.album}',
                    f'\nDuration: {output.duration}',
                ]

                if show_tech:
                    lines += [
                        f'\nBitrate: {output.bitrate} kbps',
                        f'Sample Rate: {output.sample_rate}',
                        f'Channels: {output.channels}',
                    ]

                lines += [
                    f'\nPath: {output.path}',
                    f'Lyric Path: {output.lyric}',
                    f'Lyric Offset: {output.lyric_offset}',
                    f'\nLibrary ID: {output.lib_id}'
                ]

                if show_aliases:
                    lines += [f"\nAliases ({output.aliases_num}): {output.aliases}"]

                if show_playlists:
                    lines += [f"\nPlaylists ({output.playlists_num}): {output.playlists}"]

                print(cli_box('\n'.join(lines)))
    else:
        print(empty_msg)