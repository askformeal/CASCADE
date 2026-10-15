import time

from src.sentinels import SENTINELS
from src import gen_response
from src.gen_response import Response
from src.backend.context import Context


def get_status(ctx: Context):
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
        'run_time': time.time() - ctx.start_time,
        'request_rate': ctx.get_request_rate()
    }
    progress = ctx.playback.get_progress()
    status['length'] = progress['length']
    status['time'] = progress['time']
    status['dev'] = ctx.dev

    return status

def status(ctx: Context, request: dict) -> Response:
    return gen_response.Success('status obtained', get_status(ctx))
