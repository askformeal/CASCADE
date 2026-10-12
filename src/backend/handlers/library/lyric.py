from pathlib import Path
from threading import Thread

from src.log import setup_logger
from src.constants.paths.log import BACKEND_LOG
from src.sentinels import SENTINELS
from src import gen_response
from src.gen_response import Response
from src.backend.context import Context
from src.utils.misc import get_song_display_name
from src.utils.lyric import parse_lyric
from .helpers import get_song, batch_fetch

logger = setup_logger(__name__, BACKEND_LOG)

def set_(ctx: Context, request: dict) -> Response:
    song = request['song']
    path = request['path']
    cwd = request.get('cwd', None)
    
    song_id = get_song(ctx, song, cwd)
    if song_id is SENTINELS.MISSING_CWD:
        return gen_response.MissingCWD()
    elif song_id is SENTINELS.NOT_IN_LIB:
        return gen_response.SongNotExist(song)
    else:
        if path == '':
            path = SENTINELS.CLEAR_META
        ctx.database.set_song_meta(song_id, 'lyric', path)
        return gen_response.Success(f'set lyric file of \"{song}\"')

def offset(ctx: Context, request: dict) -> Response:
    song = request['song']
    offset = request['offset']
    cwd = request.get('cwd', None)
    
    song_id = get_song(ctx, song, cwd)
    if song_id is SENTINELS.MISSING_CWD:
        return gen_response.MissingCWD()
    elif song_id is SENTINELS.NOT_IN_LIB:
        return gen_response.SongNotExist(song)
    else:
        ctx.database.set_song_meta(song_id, 'offset', offset)
        return gen_response.Success(f'set lyric offset of \"{song}\"')

def show(ctx: Context, request: dict) -> Response:
    song = request['song']
    cwd = request.get('cwd', None)

    song_id = get_song(ctx, song, cwd)
    if song_id is SENTINELS.MISSING_CWD:
        return gen_response.MissingCWD()
    elif song_id is SENTINELS.NOT_IN_LIB:
        return gen_response.SongNotExist(song)
    else:
        song_info = ctx.database.get_song_info(song_id)[0]
        lyric_path = song_info.get('lyric', None)
    
        if lyric_path is None:
            return gen_response.LyricNotExist()
        else:
            lyric = parse_lyric(lyric_path)
            if lyric is SENTINELS.FILE_IO_FAILED:
                return gen_response.FileIOFailed(lyric_path)
            else:
                attachment = {'path': lyric_path, 'lyric': lyric}
                return gen_response.Success('lyric obtained', attachment=attachment)

def fetch(ctx: Context, request: dict) -> Response:
    songs = request['songs']
    cwd = request.get('cwd', None)

    failed = []
    args = []

    if len(songs) == 0:
        return gen_response.EmptyList('songs')
    else:
        for song in songs:
            song_id = get_song(ctx, song, cwd)
            if song_id is SENTINELS.MISSING_CWD:
                failed.append(gen_response.MissingCWD())
            elif song_id is SENTINELS.NOT_IN_LIB:
                failed.append(gen_response.SongNotExist(song))
            else:
                info = ctx.database.get_song_info(song_id)[0]

                path = str(Path(info['path']).with_suffix('.lrc'))

                name = get_song_display_name(info)
                artist = info.get('artist', None)
                if artist is None:
                    artist = ''

                search_term = f'{name} {artist}'.strip()
                args.append((song_id, song, path, search_term))

        if len(songs) - len(failed) > 0:
            Thread(target=lambda: batch_fetch(ctx, args), daemon=True).start()

        return gen_response.BatchAuto('Started fetching', len(failed), len(songs), failed=failed)
