from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import syncedlyrics

from src.log import setup_logger
from src.constants.paths.log import BACKEND_LOG
from src.constants.backend import LYRIC_FETCH_MAX_WORKERS
from src.constants.misc import ENCODING
from src import gen_response
from src.backend.context import Context
from src.sentinels import SENTINELS, Sentinel
from src.utils.file_extract import extract_file_meta
from src.utils.misc import verify_path_format
from src.utils.time_ import format_time

logger = setup_logger(__name__, BACKEND_LOG)

def get_song(ctx: Context, song: str, cwd: str | None) -> int | Sentinel: # try to get song id from database
    id = ctx.database.get_song_via_alias(song)
    if id is not SENTINELS.ALIAS_NOT_FOUND:
        logger.debug(f'Got song ID {id} via alias {song}')
        return id

    elif song.isdecimal() and ctx.database.song_exists(int(song)): # isdecimal rules out floats
        logger.debug(f'Got song ID {int(song)} via song ID') # sure, why not
        return int(song)

    elif cwd is not None:
        path = Path(cwd) / song
        id = ctx.database.get_song_via_path(str(path))
        if id is not SENTINELS.SONG_NOT_FOUND:
            logger.debug(f'Got song ID {id} via path {path}')
            return id
        else:
            return SENTINELS.NOT_IN_LIB
    else:
        return SENTINELS.MISSING_CWD

def get_song_playlist_names(ctx: Context, song_id: int) -> list[str]:
    playlist_ids = ctx.database.get_song_playlists(song_id)
    playlist_info = ctx.database.get_playlists_info(playlist_ids)
    return list(map(lambda pl: pl['name'], playlist_info))

def insert_songs_aliases(ctx: Context, info: list[dict]) -> list[dict]:
    for i, song in enumerate(info):
        aliases = ctx.database.get_song_aliases(song['id'])
        info[i]['aliases'] = aliases
    return info

def insert_songs_playlist_names(ctx: Context, info: list[dict]) -> list[dict]:
    for i, song in enumerate(info):
        playlists_id = ctx.database.get_song_playlists(song['id'])
        playlists_info = ctx.database.get_playlists_info(playlists_id)
        info[i]['playlists'] = list(map(lambda pl: pl['name'], playlists_info))
    return info

def add_song(
        ctx: Context,
        path: str, 
        set_meta: bool = True,
        bind_alias: bool = True, 
        set_lyric: bool = True,
        alias: str | None = None,
        cwd: str | None = None,
        loose_path: bool = False,
        return_id: bool = False
        ) -> tuple[int, gen_response.Response] | gen_response.Response:
    song_id = None
    if not Path(path).is_absolute():
        if cwd is None:
            response = gen_response.MissingCWD()
            path = None
        else:
            path = str(Path(cwd) / path)

    if path is not None and (Path(path).is_file() or (loose_path and verify_path_format(path))):
        add_response = None
        alias_response = None
        meta_response = None
        auto_alias_response = None
        song_id, ignored = ctx.database.add_song(path)
        if not ignored:
            add_response = gen_response.Success(f'added song \"{path}\" to library')

            # --- manual alias ---
            if alias is not None:
                result = ctx.database.bind_alias(song_id, alias)
                if result is SENTINELS.ALIAS_EXISTS:
                    alias_msg = f'can not bind alias \"{alias}\" to the song'
                else:
                    alias_msg = f'bound alias \"{alias}\" to the song'
                alias_response = gen_response.Success(alias_msg)

            meta = extract_file_meta(path)

            # --- auto set metadata ---
            if set_meta:
                count = 0
                for tag, value in meta.items():
                    ctx.database.set_song_meta(song_id, tag, value)
                    if value is not None:
                        count += 1
                meta_response = gen_response.Success(f'set {count} metadata of the song from file')
            else:
                duration = meta.get('duration', None)
                bitrate = meta.get('bitrate', None)
                sample_rate = meta.get('sample_rate', None)
                channels = meta.get('channels', None)

                ctx.database.set_song_meta(song_id, 'duration', duration)
                ctx.database.set_song_meta(song_id, 'bitrate', bitrate)
                ctx.database.set_song_meta(song_id, 'sample_rate', sample_rate)
                ctx.database.set_song_meta(song_id, 'channels', channels)

                meta_response = gen_response.Success(f'set duration to {format_time(duration)}, bitrate to {bitrate}, sample rate to {sample_rate} and channels to {channels}')

            # --- auto bind alias ---
            if bind_alias:
                name = meta.get('name', None)
                if name is not None and not ctx.database.alias_exists(name):
                    ctx.database.bind_alias(song_id, name)
                    bind_msg = f'bound alias \"{name}\" from song name in metadata'
                else:
                    logger.info(f'Name metadata of song with id {song_id} and path {path} does not exist or is already used. Now try to use filename instead')
                    name = Path(path).stem
                    result = ctx.database.bind_alias(song_id, name)
                    if result is SENTINELS.ALIAS_EXISTS:
                        logger.info(f'Can not find a suitable alias for song with id {song_id} and path {path}. Auto alias binding canceled')
                        bind_msg = f'can not find and bind an available alias for the song automatically'
                    else:
                        bind_msg = f'bound alias \"{name}\" from filename'
                auto_alias_response = gen_response.Success(bind_msg)

            # --- auto set lyric file ---
            if set_lyric:
                lyric_path = Path(path).with_suffix('.lrc')
                if lyric_path.is_file():
                    ctx.database.set_song_meta(song_id, 'lyric', str(lyric_path))

            response = add_response + alias_response + meta_response + auto_alias_response
        else:
            response = gen_response.Failed(f'a song of the same path already exists in library')
    else:
        response = gen_response.InvalidPath(path)

    if return_id:
        return song_id, response
    else:
        return response

def batch_fetch(ctx: Context, args: list[tuple]):
    logger.info(f'Start fetching lyric for {len(args)} song(s)...')
    batch_task_index = ctx.task.add_task(max_progress=len(args), name=f'Fetch lyrics for {len(args)} songs')

    with ThreadPoolExecutor(max_workers=LYRIC_FETCH_MAX_WORKERS) as pool:
        results = list(pool.map(lambda arg: fetch_lyric(ctx, batch_task_index, *arg), args))

    ok = 0
    for result in results:
        song_id, song_name, path, lrc, task_index, error = result
        
        if lrc is None:
            logger.info(f'Failed to fetch lyric for \"{song_name}\": can not find lyric')
            ctx.task.task_failed(task_index, 'Can not find lyric')
        
        elif lrc is SENTINELS.LYRIC_FETCH_ERROR:
            ctx.task.task_failed(task_index, f'Error while fetching: {error}')

        else:
            ctx.task.log_task(task_index, 'Lyric obtained')
            try:
                with open(path, 'w', encoding=ENCODING) as f:
                    f.write(lrc)
                    
            except OSError as e:
                logger.warning(f'Failed to fetch lyric for \"{song_name}\": failed to write into {path}: \"{e}\"')
                ctx.task.task_failed(task_index, f'Failed to write into {path}: {e}')

            else:
                ctx.database.set_song_meta(song_id, 'lyric', path)
                logger.info(f'Fetched lyric for \"{song_name}\": saved to {path}')
                ctx.task.task_succeed(task_index, f'Wrote into {path}, fetching completed')
                ok += 1

    ctx.notify(f'[{ok}/{len(results)}] lyric(s) fetched successfully')
    ctx.task.log_task(batch_task_index, f'[{ok}/{len(results)}] fetched successfully')
    if ok > 0:
        ctx.task.task_succeed(batch_task_index)
    else:
        ctx.task.task_failed(batch_task_index)

def fetch_lyric(
        ctx: Context,
        batch_task_index: int,
        song_id: int,
        song_name: str,
        path: str,
        search_term: str
        ) -> tuple[int, str, str, str | None | Sentinel, int, Exception | None]:

    error = None

    logger.info(f'Started fetching lyric with: {search_term}')
    task_index = ctx.task.add_task(name=f'Fetch lyric: {search_term}')
    try:
        lrc = syncedlyrics.search(
            search_term,
            synced_only=True,
        )
    except Exception as e:
        logger.warning(f'Failed to fetch lyric with {search_term}: {e}')
        lrc = SENTINELS.LYRIC_FETCH_ERROR
        error = e
    else:
        logger.info(f'Lyric fetched with: {search_term}')

    ctx.task.nudge_task_progress(batch_task_index)
    return song_id, song_name, path, lrc, task_index, error
