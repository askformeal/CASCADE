import time
import random
from pathlib import Path

from src.log import setup_logger
from src.constants.paths import BACKEND_LOG_PATH

from src.sentinels import SENTINELS
from src import gen_response
from src.utils.misc import sort_songs
from src.utils.time_ import format_time

logger = setup_logger(__name__, BACKEND_LOG_PATH)

def get_status(ctx):
    player_status = {
        SENTINELS.PLAYING: 'playing',
        SENTINELS.PAUSED: 'paused',
        SENTINELS.STOPPED: 'stopped',
        SENTINELS.PLAYER_INVALID: None
    }.get(ctx.playback.get_status(), None)
    
    if ctx.playback.current_song_info is None:
        info = {}
        playlist_len = None
        current_num = None
    else:
        info = ctx.playback.get_playing_info()
        playlist_len = len(ctx.playback.current_song_info)
        current_num = ctx.playback.current_song_num

    if ctx.playback.current_playlist is SENTINELS.PLAY_ALL:
        playlist_name = None
        playing_all = True
    else:
        playing_all = False
        if ctx.playback.current_playlist is not None:
            playlist_info = ctx.database.get_playlists_info(ctx.playback.current_playlist)
            if len(playlist_info) > 0:
                playlist_name = playlist_info[0]['name']
            else:
                playlist_name = None
        else:
            playlist_name = None
    
    status = {
        'id': info.get('id', None),
        'path': info.get('path', None),
        'name': info.get('name', None),
        'artist': info.get('artist', None),
        'album': info.get('album', None),
        'duration': info.get('duration', None),
        'bitrate': info.get('bitrate', None),
        'sample_rate': info.get('sample_rate', None),
        'channels': info.get('channels', None),
        'lyric_path': info.get('lyric', None),
        'in_library': ctx.playback.current_song_in_lib,
        'player_status': player_status,
        'volume': ctx.playback.get_volume(),
        'mute': ctx.playback.get_mute(),
        'shuffle': ctx.playback.shuffle,
        'loop': ctx.playback.loop,
        'reverse': ctx.playback.reverse,
        'online_lyric': ctx.playback.online_lyric,
        'playlist_len': playlist_len,
        'current_num': current_num,
        'playlist_name': playlist_name,
        'playing_all': playing_all,
        'engine': ctx.playback.get_engine_name(),
        'run_time': time.time() - ctx.start_time
    }
    progress = ctx.playback.get_progress()
    status['length'] = progress['length']
    status['time'] = progress['time']
    status['dev'] = ctx.dev

    return status

def get_current_songs(ctx):
    if ctx.playback.current_song_info is not None:
        return ctx.playback.current_song_info.copy()
    else:
        return []

def get_current_lyric(ctx):
    ctx.playback.update_lyric()
    lyric = ctx.playback.lyric
    lyric['offset_overlay'] = ctx.playback.offset_overlay

    return lyric

def open_song(ctx, song, type_, cwd=None) -> gen_response.Response:
    result = _resolve_open(ctx, song, type_, cwd)
    if result is SENTINELS.INVALID_OPEN:
        if type_ == 'auto':
            type_ = 'a song in library, a playlist or a file'
        else:
            type_ = f'a {type_}'
        return gen_response.Failed(f'failed to parse \"{song}\" as {type_}')
    else:
        type_, reference = result
    
    logger.debug(f'Resolved \"{song}\" into reference \"{reference}\" of type {type_}')
    
    return open_type(ctx, type_, reference)

def open_type(ctx, type_, reference):
    if type_ == 'song':
        song_info = ctx.database.get_song_info(reference)
        info_to_set = (song_info,)
        paths_to_load = [song_info[0]['path']]

    elif type_ == 'playlist':
        ids = ctx.database.get_playlist_songs(reference)
        if ids is SENTINELS.PLAYLIST_EMPTY:
            return gen_response.Failed(f'can not open playlist because it is empty')
        else:
            info = ctx.database.get_song_info(ids)
            info = sort_songs(info)
            info_to_set = (info,)
            paths_to_load = list(map(lambda i: i['path'], info))
    
    elif type_ == 'file':
        if Path(reference).is_file():
            info_to_set = ([{'path': reference}], False)
            paths_to_load = [reference]
        else:
            return gen_response.FileIOFailed(f'open song', reference, "it does not exist")
        
    if ctx.playback.current_song_info is None:
        current_paths = []
    else:
        current_paths = list(map(lambda s: s['path'], ctx.playback.current_song_info))

    if len(paths_to_load) == 1 and paths_to_load[0] in current_paths and type_ == 'song':
        num = current_paths.index(paths_to_load[0])
        ctx.playback.current_song_info[num] = info_to_set[0][0]
        response = gen_response.Success('song in current playlist. try to switch')
        response.append(switch_song(ctx, num), joiner='->')
    else:
        ctx.playback.set_current_song(*info_to_set)
        response = _load_paths(ctx, paths_to_load)

        if response.ok():
            ctx.database.set_setting('last_is_all', '0')
            ctx.database.set_setting('last_type', type_)
            ctx.database.set_setting('last_reference', reference)

            if type_ == 'playlist':
                ctx.playback.current_playlist = reference
                last_num = ctx.database.get_playlist_last_num(reference)
                if last_num not in (None, SENTINELS.PLAYLIST_NOT_FOUND):
                    response += gen_response.Success('last played number detected, switching')
                    response.append(switch_song(ctx, last_num), joiner='->')
                else:
                    ctx.playback.set_current_num(0)
            else:
                ctx.playback.current_playlist = None                

    return response

def _resolve_open(ctx, song, type_, cwd):
    if type_ in ('song', 'auto'):
        ok, result = _resolve_song(ctx, song, cwd)
        if ok:
            return 'song', result
        
    if type_ in ('playlist', 'auto'):
        ok, result = _resolve_playlist(ctx, song)
        if ok:
            return 'playlist', result
    
    if type_ in ('file', 'auto'):
        ok, result = _resolve_path(song, cwd)
        if ok: 
            return 'file', result
    
    return SENTINELS.INVALID_OPEN

def _resolve_song(ctx, song, cwd):
    from ..library.helpers import get_song
    id_ = get_song(ctx, song, cwd)
    if id_ is SENTINELS.NOT_IN_LIB:
        return False, gen_response.SongNotExist(f'resolve {song}')
    elif id_ is SENTINELS.MISSING_CWD:
        return False, gen_response.MissingCWD(f'resolve {song}')
    else:
        return True, id_

def _resolve_playlist(ctx, playlist):
    id_ = ctx.database.get_playlist_via_name(playlist)
    if id_ is SENTINELS.PLAYLIST_NOT_FOUND:
        return False, gen_response.PlaylistNotExist(f'resolve {playlist}')
    else:
        return True, id_

def _resolve_path(path, cwd):
    if Path(path).is_absolute():
        path = Path(path)
    else:
        if cwd is None:
            return False, gen_response.MissingCWD(f'resolve {path}')
        else:
            path = Path(cwd) / path

    return True, str(path)


def play_all_songs(ctx):
    info = ctx.database.get_all_song_info()
    if len(info) > 0:
        info = sort_songs(info)
        ctx.playback.set_current_song(info, True)
        paths = list(map(lambda x: x['path'], info))
        response = _load_paths(ctx, paths)
        if response.ok():
            ctx.database.set_setting('last_is_all', '1')
            ctx.playback.current_playlist = SENTINELS.PLAY_ALL
            last_num = ctx.database.get_setting('last_play_all_num')
            if last_num not in (SENTINELS.SETTING_NOT_FOUND, None):
                last_num = int(last_num)

                response += gen_response.Success('last played number detected, switching')
                response.append(switch_song(ctx, last_num), joiner='->')
            else:
                ctx.playback.set_current_num(0)
    else:
        response = gen_response.Failed('can not open all songs because there is none in library')
    return response

def switch_song(ctx, num) -> gen_response.Response:
    max_num = ctx.playback.get_media_len()
    if num >= max_num:
        num_to_load = max_num - 1 # 9999999999 will switch the last song
    elif num < 0:
        num_to_load = max(max_num + num, 0) # -3 will switch the third from last song, -9999999999 will switch to the first song
    else:
        num_to_load = num
    result = ctx.playback.switch_to(num_to_load)

    if result is SENTINELS.SUCCESS:
        ctx.playback.set_current_num(ctx.playback.get_number())

    response = {
        SENTINELS.SUCCESS: gen_response.Success(f'switched to the {num+1}nd song in current playlist: {ctx.playback.get_current_display_name()}'),
        SENTINELS.PLAYER_EMPTY: gen_response.PlayerEmpty(f'switch to the {num+1}nd song in current playlist'),
        SENTINELS.ENGINE_ERROR: gen_response.EngineError(f'switch to the {num+1}nd song in current playlist'),
        SENTINELS.PLAYER_TIMEOUT: gen_response.PlayerTimeout(f'switch to the {num+1}nd song in current playlist'),
        SENTINELS.FILE_IO_FAILED: gen_response.InvalidAudioFile(f'switch to the {num+1}nd song in current playlist')
    }[result]
    if result is SENTINELS.SUCCESS:
        response += _jump_to_memorized_pos(ctx)

    return response

def del_current_pos(ctx):
    if ctx.playback.current_song_info is not None:
        path = ctx.playback.get_playing_info()['path']
        ctx.database.del_pos(path)
    else:
        logger.warning('backend:del_current_pos is triggered before any song is loaded')

def _jump_to_memorized_pos(ctx) -> gen_response.Response:
    path = ctx.playback.get_playing_info()['path']
    pos = ctx.database.get_pos(path)
    if pos is not SENTINELS.POS_NOT_FOUND:
        response = gen_response.Success('try to jump to memorized pos')
        response.append(jump_to_pos(ctx, pos), joiner='->')
        return response
    else:
        return gen_response.Success(f'no memorized position')

def jump_to_pos(ctx, pos) -> gen_response.Response:
    result = ctx.playback.jump_pos(pos)
    return {
        SENTINELS.SUCCESS: gen_response.Success(f'jumped to {format_time(pos)}'),
        SENTINELS.POS_TOO_LATE: gen_response.Failed(f'can not jumps to {format_time(pos)} because it is later than the end of the current song'), 
        SENTINELS.INVALID_PLAYER_STATE: gen_response.NotPlayingPaused('jump to progress')
    }[result]

def replay_song(ctx) -> gen_response.Response:
    result = ctx.playback.jump_pos(0)
    return {
        SENTINELS.SUCCESS: gen_response.Success('jumped to beginning'),
        SENTINELS.POS_TOO_LATE: gen_response.PosTooLate('jump to beginning'), # is this even possible?
        SENTINELS.INVALID_PLAYER_STATE: gen_response.NotPlayingPaused('jump to beginning')
    }[result]

def _load_paths(ctx, paths, jump_to_mem=True) -> gen_response.Response:
    result = ctx.playback.load_paths(paths)
    response = {
        SENTINELS.SUCCESS: gen_response.Success(f'opened song/playlist'),
        SENTINELS.PLAYER_LOAD_EMPTY: gen_response.Failed('can not load empty list of songs'),
        SENTINELS.ENGINE_ERROR: gen_response.EngineError('load path(s)'),
        SENTINELS.PLAYER_TIMEOUT: gen_response.PlayerTimeout('load path(s)'),
        SENTINELS.FILE_IO_FAILED: gen_response.InvalidAudioFile('load path(s)')
    }[result]
    if jump_to_mem and result is SENTINELS.SUCCESS:
        response += _jump_to_memorized_pos(ctx)
    return response

def stop_player(ctx) -> gen_response.Response:
    result = ctx.playback.stop()
    return {
        SENTINELS.SUCCESS: gen_response.Success('player stopped'),
        SENTINELS.ENGINE_ERROR: gen_response.EngineError('stop player'),
        SENTINELS.PLAYER_TIMEOUT: gen_response.PlayerTimeout('stop player')
    }[result]

def switch_shuffle(ctx, direction): # direction: 1 / -1
    if len(ctx.playback.shuffle_order) > 0:
        shuffle_num = ctx.playback.shuffle_order.index(ctx.playback.current_song_num)
        shuffle_num += direction
        if shuffle_num >= len(ctx.playback.shuffle_order):
            shuffle_num = 0
            random.shuffle(ctx.playback.shuffle_order)
        elif shuffle_num < 0:
            shuffle_num = len(ctx.playback.shuffle_order) - 1
        return ctx.playback.shuffle_order[shuffle_num]
    else:
        return SENTINELS.PLAYER_EMPTY

def remove_from_current(ctx, path) -> gen_response.Response:
    if ctx.playback.current_song_info is not None:
        paths = list(map(lambda s: s['path'], ctx.playback.current_song_info))
        if path in paths:
            removed_num = paths.index(path)
            paths.remove(path)
            ctx.playback.current_song_info = ctx.playback.current_song_info[:removed_num] + ctx.playback.current_song_info[removed_num+1:]
            if len(paths) > 0:
                num = ctx.playback.current_song_num
                if removed_num < num: # removed before current
                    num -= 1
                elif removed_num == num:
                    if num >= len(paths):
                        num = len(paths) - 1

                response = _load_paths(ctx, paths, jump_to_mem=False)
                response += switch_song(ctx, num)
                return response
            else:
                ctx.playback.current_song_info = None
                ctx.playback.current_song_num = None
                ctx.playback.current_song_in_lib = False
                ctx.playback.current_playlist = None
                return stop_player(ctx)
        else:
            return gen_response.Success('path not in current playlist') # not that anyone will actually read this but, you know, for good measure
    else:
        return gen_response.Success('current playlist empty') # same as above

def loop_play(ctx):
    result = ctx.playback.switch_to(ctx.playback.get_number())
    return {
        SENTINELS.SUCCESS: gen_response.Success('replayed current song'),
        SENTINELS.ENGINE_ERROR: gen_response.EngineError('replayed current song'),
        SENTINELS.PLAYER_TIMEOUT: gen_response.PlayerTimeout('replayed current song'),
        SENTINELS.FILE_IO_FAILED: gen_response.InvalidAudioFile('replayed current song')
    }[result]
