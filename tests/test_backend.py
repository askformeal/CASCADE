import os
import wave

import pytest

from src.sentinels import SENTINELS


def _request(backend, action, **extra):
    request = {'action': action, 'cwd': os.getcwd()}
    request.update(extra)
    return backend.dispatch(request)


def _run_buffered_request(backend):
    """Pop one request queued by the backend itself and dispatch it, like _flush_buffer does."""
    request, _ = backend.dispatch_buffer.get()
    return request, backend.dispatch(request)


def _playlist_song_ids(database, playlist_id):
    """get_playlist_songs returns song info dicts now; compare ids only."""
    songs = database.get_playlist_songs(playlist_id)
    ids = []
    for song in songs:
        ids.append(song['id'])
    return ids


def test_status_before_open(backend):
    response = _request(backend, 'status')
    assert response['code'] == 0
    assert response['attachment']['path'] is None
    assert response['attachment']['in_library'] is False


def test_status_missing_cwd(backend):
    # cwd validation now lives inside actions that need it (open/lib.*),
    # not at the global dispatch gate; status never needs cwd.
    response = _request(backend, 'status')
    assert response['code'] == 0


def test_invalid_action(backend):
    response = _request(backend, 'bogus')
    assert response['code'] == 1
    assert 'unknown action received: "bogus"' in response['msg']


def test_missing_action_key(backend):
    response = backend.dispatch({'cwd': os.getcwd()})
    assert response['code'] == 1
    assert 'action' in response['msg']


def test_request_not_dict(backend):
    response = backend.dispatch(['not', 'a', 'dict'])
    assert response['code'] == 1
    assert 'not a dictionary' in response['msg']


def test_missing_required_key(backend):
    response = _request(backend, 'open')
    assert response['code'] == 1
    assert 'song' in response['msg']


def test_guards_before_open(backend):
    assert _request(backend, 'pause')['code'] == 1
    assert _request(backend, 'resume')['code'] == 1
    assert _request(backend, 'toggle')['code'] == 1


def test_list_before_open(backend):
    response = _request(backend, 'list')
    assert response['code'] == 0
    assert response['attachment'] == []


def test_list_after_open_raw_path(backend, audio_file):
    _request(backend, 'open', song=audio_file)
    response = _request(backend, 'list')
    assert response['code'] == 0
    assert response['attachment'] == [{'path': audio_file}]


def test_list_after_open_lib_song(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    _request(backend, 'open', song=audio_file)
    response = _request(backend, 'list')
    assert response['code'] == 0
    assert len(response['attachment']) == 1
    assert response['attachment'][0]['id'] == 1
    assert response['attachment'][0]['path'] == audio_file


def test_list_after_open_playlist(backend, audio_file):
    _create_playlist_with_song(backend, audio_file, 'workout')
    _request(backend, 'open', song='workout')
    response = _request(backend, 'list')
    assert response['code'] == 0
    assert len(response['attachment']) == 1
    assert response['attachment'][0]['path'] == audio_file


def test_switch_missing_number(backend):
    response = _request(backend, 'switch')
    assert response['code'] == 1
    assert 'number' in response['msg']


def test_switch_before_open(backend):
    response = _request(backend, 'switch', number=1)
    assert response['code'] == 1
    assert 'no songs are being played' in response['msg']


def _open_two_song_playlist(backend, audio_file, tmp_path):
    """Open a playlist with two songs sorted as [a, b] by basename."""
    first = audio_file
    second = str(tmp_path / 'test_b.wav')
    _make_wav(second)
    _open_playlist_with_songs(backend, [first, second], 'pair')
    return first, second


def test_switch_to_number(backend, audio_file, tmp_path):
    first, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    response = _request(backend, 'switch', number=1)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first

    response = _request(backend, 'switch', number=2)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_switch_zero_means_first(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    response = _request(backend, 'switch', number=0)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first


def test_switch_too_large_goes_to_last(backend, audio_file, tmp_path):
    _, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    response = _request(backend, 'switch', number=999999)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_switch_negative_counts_from_last(backend, audio_file, tmp_path):
    first, second = _open_two_song_playlist(backend, audio_file, tmp_path)

    response = _request(backend, 'switch', number=-1)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second

    response = _request(backend, 'switch', number=-2)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first


def test_switch_negative_too_large_goes_to_first(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    response = _request(backend, 'switch', number=-999)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first


def test_dice_before_open(backend):
    response = _request(backend, 'dice')
    assert response['code'] == 1
    assert 'no songs are being played' in response['msg']


def test_dice_single_song(backend, audio_file):
    _request(backend, 'open', song=audio_file)
    response = _request(backend, 'dice')
    assert response['code'] == 1
    assert 'only one song' in response['msg']


def _open_three_song_playlist(backend, audio_file, tmp_path):
    """Open a playlist with three songs sorted as [a, b, c] by basename."""
    first = audio_file
    second = str(tmp_path / 'test_b.wav')
    third = str(tmp_path / 'test_c.wav')
    _make_wav(second)
    _make_wav(third)
    _open_playlist_with_songs(backend, [first, second, third], 'trio')
    return first, second, third


def test_dice_skips_current_song(backend, audio_file, tmp_path, monkeypatch):
    _, second, _ = _open_three_song_playlist(backend, audio_file, tmp_path)
    assert backend.playback.current_song_num == 0

    pool_seen = []
    def fake_choice(seq):
        pool_seen.extend(seq)
        return seq[0]
    from src.backend.handlers.playback import sequence
    monkeypatch.setattr(sequence.random, 'choice', fake_choice)
    response = _request(backend, 'dice')
    assert response['code'] == 0
    assert pool_seen == [1, 2]  # current song (0) excluded from the pool
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_open_raw_path(backend, audio_file):
    response = _request(backend, 'open', song=audio_file)
    assert response['code'] == 0
    assert backend.playback.current_song_in_lib is False
    status = _request(backend, 'status')
    assert status['attachment']['path'] == audio_file


def test_open_missing_file(backend):
    response = _request(backend, 'open', song='nonexistent_song.flac')
    assert response['code'] == 1
    # the path resolved fine, so the failure names the resolved absolute path
    assert 'nonexistent_song.flac' in response['msg']
    assert 'it does not exist' in response['msg']


def test_open_without_cwd_not_playlist(backend):
    """Auto resolution without cwd fails with the single shared parse-failure
    message. The specific sub-reasons (song / playlist / missing cwd) are
    deliberately not surfaced: auto is a guess, and its failure must not claim
    to know which guess was right."""
    response = backend.dispatch({'action': 'open', 'song': 'not_a_playlist_either'})
    assert response['code'] == 1
    assert 'can not parse "not_a_playlist_either"' in response['msg']
    assert 'a song in library, a playlist or a file' in response['msg']


def test_open_via_library_path(backend, audio_file):
    database = backend.database
    database.add_song(audio_file)
    response = _request(backend, 'open', song=audio_file)
    assert response['code'] == 0
    assert backend.playback.current_song_in_lib is True


def test_open_via_alias(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'test_alias')
    response = _request(backend, 'open', song='test_alias')
    assert response['code'] == 0
    assert backend.playback.current_song_in_lib is True
    assert backend.playback.current_song_info[0]['path'] == audio_file


def test_open_alias_priority_over_path(backend, audio_file, tmp_path):
    """Alias lookup must win even if the alias string is not a real path."""
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'test_alias')
    response = _request(backend, 'open', song='test_alias')
    assert response['code'] == 0
    assert backend.playback.current_song_info[0]['id'] == song_id


def test_open_via_song_id(backend, audio_file):
    """A numeric string that matches a library song ID resolves to that song."""
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    response = _request(backend, 'open', song=str(song_id))
    assert response['code'] == 0
    assert backend.playback.current_song_info[0]['id'] == song_id


def test_open_song_id_not_found_falls_back_to_path(backend, audio_file):
    """A numeric string with no matching song ID falls through to path lookup."""
    database = backend.database
    database.add_song(audio_file)
    response = _request(backend, 'open', song='999')
    assert response['code'] == 1
    assert '999' in response['msg']
    assert 'it does not exist' in response['msg']


def test_open_superscript_does_not_crash(backend, audio_file):
    """Superscript/circled digits pass isdigit but not isdecimal; must not crash int()."""
    database = backend.database
    database.add_song(audio_file)
    response = _request(backend, 'open', song='²')
    assert response['code'] == 1
    assert '²' in response['msg']


def test_open_explicit_song_type_does_not_fall_through(backend, audio_file, tmp_path):
    """type='song' must not fall back to the playlist or file branch."""
    _open_two_song_playlist(backend, audio_file, tmp_path)
    response = _request(backend, 'open', song='pair', type='song')
    assert response['code'] == 1
    assert 'can not parse "pair" as a song' in response['msg']


def test_open_explicit_playlist_type_wins_over_same_named_alias(backend, audio_file, tmp_path):
    """The named case this feature exists for: a playlist shadowed by an alias.

    Auto resolves the alias (song branch is tried first); an explicit
    type='playlist' reaches the playlist that auto can never reach.
    """
    _open_two_song_playlist(backend, audio_file, tmp_path)
    shadow_path = str(tmp_path / 'shadow.wav')
    _make_wav(shadow_path)
    database = backend.database
    shadow_id, _ = database.add_song(shadow_path)
    database.bind_alias(shadow_id, 'pair')

    _request(backend, 'open', song='pair')
    assert backend.playback.current_song_info[0]['id'] == shadow_id

    response = _request(backend, 'open', song='pair', type='playlist')
    assert response['code'] == 0
    assert backend.playback.current_playlist is not None
    status = _request(backend, 'status')
    assert status['attachment']['playlist_len'] == 2


def test_open_explicit_file_type_loads_out_of_library(backend, audio_file):
    """type='file' loads the file as a raw path even when the library knows it."""
    database = backend.database
    database.add_song(audio_file)
    response = _request(backend, 'open', song=audio_file, type='file')
    assert response['code'] == 0
    assert backend.playback.current_song_in_lib is False
    status = _request(backend, 'status')
    assert status['attachment']['path'] == audio_file


def test_open_invalid_type_rejected(backend):
    response = _request(backend, 'open', song='anything', type='banana')
    assert response['code'] == 1
    assert 'type' in response['msg']


def test_open_type_defaults_to_auto(backend, audio_file):
    """A missing key and an explicit None both fall back to the 'auto' default."""
    song_id, _ = backend.database.add_song(audio_file)

    response = backend.dispatch({'action': 'open', 'song': str(song_id), 'cwd': os.getcwd()})
    assert response['code'] == 0
    assert backend.playback.current_song_info[0]['id'] == song_id

    response = _request(backend, 'open', song=str(song_id), type=None)
    assert response['code'] == 0
    assert backend.playback.current_song_info[0]['id'] == song_id


def test_open_alias_priority_over_song_id(backend, audio_file, tmp_path):
    """An alias that looks like a number wins over a song ID."""
    _make_wav(tmp_path / 'other.wav')
    database = backend.database
    first_id, _ = database.add_song(audio_file)
    second_id, _ = database.add_song(str(tmp_path / 'other.wav'))
    database.bind_alias(second_id, str(first_id))
    response = _request(backend, 'open', song=str(first_id))
    assert response['code'] == 0
    assert backend.playback.current_song_info[0]['id'] == second_id


def test_lib_del_by_id(backend, audio_file):
    """lib.del resolves numeric strings as song IDs too (shared _get_song)."""
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    response = _request(backend, 'lib.del', songs=[str(song_id)])
    assert response['code'] == 0
    assert not database.song_exists(song_id)


def test_lib_add(backend, audio_file):
    response = _request(backend, 'lib.add', paths=[audio_file])
    assert response['code'] == 0
    assert backend.database.song_exists(1)


def test_lib_add_duplicate(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.add', paths=[audio_file])
    assert response['code'] == 1
    assert 'already exists' in response['failed'][0]['msg']


def test_lib_add_missing_file(backend):
    response = _request(backend, 'lib.add', paths=[r'C:\does\not\exist.flac'])
    assert response['code'] == 1
    assert 'valid and existing path' in response['failed'][0]['msg']


def test_lib_add_batch_multiple(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    _make_wav(tmp_path / 'b.wav')
    response = _request(backend, 'lib.add', paths=[str(tmp_path / 'a.wav'), str(tmp_path / 'b.wav')])
    assert response['code'] == 0
    assert '2/2' in response['msg']
    assert backend.database.song_exists(1)
    assert backend.database.song_exists(2)


def test_lib_add_batch_partial_failure(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    response = _request(backend, 'lib.add', paths=[str(tmp_path / 'a.wav'), r'C:\does\not\exist.flac'])
    assert response['code'] == 0
    assert '1/2' in response['msg']
    assert len(response['failed']) == 1
    assert 'valid and existing path' in response['failed'][0]['msg']


def test_lib_add_batch_all_failed(backend):
    response = _request(backend, 'lib.add', paths=[r'C:\does\not\exist1.flac', r'C:\does\not\exist2.flac'])
    assert response['code'] == 1
    assert '0/2' in response['msg']
    assert len(response['failed']) == 2


def test_lib_add_batch_empty_paths(backend):
    response = _request(backend, 'lib.add', paths=[])
    assert response['code'] == 1
    assert 'empty list of paths' in response['msg']


def test_lib_add_loose_path_nonexistent(backend, tmp_path):
    ghost = str(tmp_path / 'ghost.flac')
    response = _request(backend, 'lib.add', paths=[ghost], loose_path=True)
    assert response['code'] == 0
    assert '1/1' in response['msg']
    assert backend.database.song_exists(1)


def test_lib_add_loose_path_directory(backend, tmp_path):
    response = _request(backend, 'lib.add', paths=[str(tmp_path)], loose_path=True)
    assert response['code'] == 0
    assert '1/1' in response['msg']
    assert backend.database.song_exists(1)


def test_lib_add_loose_path_rejects_illegal_format(backend):
    response = _request(backend, 'lib.add', paths=[r'C:\a<b>.flac'], loose_path=True)
    assert response['code'] == 1
    assert len(response['failed']) == 1


def test_lib_add_strict_still_rejects_missing(backend, tmp_path):
    ghost = str(tmp_path / 'ghost.flac')
    response = _request(backend, 'lib.add', paths=[ghost])
    assert response['code'] == 1
    assert len(response['failed']) == 1


def test_lib_add_batch_alias_mismatch(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    _make_wav(tmp_path / 'b.wav')
    response = _request(backend, 'lib.add', paths=[str(tmp_path / 'a.wav'), str(tmp_path / 'b.wav')], aliases=['only_one'])
    assert response['code'] == 1
    assert 'not of the same number' in response['msg']


def test_lib_add_batch_with_aliases(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    _make_wav(tmp_path / 'b.wav')
    response = _request(backend, 'lib.add', paths=[str(tmp_path / 'a.wav'), str(tmp_path / 'b.wav')], aliases=['alpha', 'beta'])
    assert response['code'] == 0
    assert '2/2' in response['msg']
    assert backend.database.get_song_via_alias('alpha') == 1
    assert backend.database.get_song_via_alias('beta') == 2


def test_lib_list_empty(backend):
    response = _request(backend, 'lib.list', show_aliases=False)
    assert response['code'] == 0
    assert response['attachment'] == []


def test_lib_list_after_add(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.list', show_aliases=False)
    assert response['code'] == 0
    assert len(response['attachment']) == 1
    assert response['attachment'][0]['path'] == audio_file
    assert 'aliases' not in response['attachment'][0]


def test_lib_list_with_show_aliases(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    _request(backend, 'lib.alias.bind', song=audio_file, aliases=['favorite'])
    response = _request(backend, 'lib.list', show_aliases=True)
    assert response['code'] == 0
    assert response['attachment'][0]['aliases'] == ['test_audio', 'favorite']


def test_lib_list_show_aliases_empty(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file], skip_alias=True)
    response = _request(backend, 'lib.list', show_aliases=True)
    assert response['code'] == 0
    assert response['attachment'][0]['aliases'] == []


def test_lib_list_with_show_playlists(backend, audio_file):
    database = backend.database
    _request(backend, 'lib.add', paths=[audio_file])
    song_id = database.get_all_song_info()[0]['id']
    playlist_id, _ = database.create_playlist('workout')
    database.add_song_to_playlist(playlist_id, song_id)
    response = _request(backend, 'lib.list', show_playlists=True)
    assert response['code'] == 0
    assert response['attachment'][0]['playlists'] == ['workout']


def test_lib_list_show_playlists_empty(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.list', show_playlists=True)
    assert response['code'] == 0
    assert response['attachment'][0]['playlists'] == []


def test_lib_list_without_show_playlists(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.list')
    assert response['code'] == 0
    assert 'playlists' not in response['attachment'][0]


def test_lib_del_by_path(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.del', songs=[audio_file])
    assert response['code'] == 0
    assert backend.database.song_exists(1) is False


def test_lib_del_by_alias(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'test_alias')
    response = _request(backend, 'lib.del', songs=['test_alias'])
    assert response['code'] == 0
    assert backend.database.song_exists(song_id) is False


def test_lib_del_not_in_library(backend):
    response = _request(backend, 'lib.del', songs=['ghost_song'])
    assert response['code'] == 1
    assert 'no such song in library' in response['failed'][0]['msg']


def test_lib_del_when_nothing_open(backend, audio_file):
    """Deleting a lib song while nothing is open must not crash (regression: Path(None))."""
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.del', songs=[audio_file])
    assert response['code'] == 0


def test_lib_del_current_song_resets_state(backend, audio_file):
    """Deleting the currently-open lib song must flip in_library back to False."""
    _request(backend, 'lib.add', paths=[audio_file])
    _request(backend, 'open', song=audio_file)
    assert backend.playback.current_song_in_lib is True

    response = _request(backend, 'lib.del', songs=[audio_file])
    assert response['code'] == 0
    assert backend.playback.current_song_in_lib is False
    assert backend.playback.current_song_info[0] == {'path': audio_file}


def test_lib_del_cascades_alias(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'test_alias')
    _request(backend, 'lib.del', songs=[audio_file])
    assert database.get_song_via_alias('test_alias') is SENTINELS.ALIAS_NOT_FOUND


def test_lib_del_batch_multiple(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    _make_wav(tmp_path / 'b.wav')
    paths = [str(tmp_path / 'a.wav'), str(tmp_path / 'b.wav')]
    _request(backend, 'lib.add', paths=paths)
    response = _request(backend, 'lib.del', songs=paths)
    assert response['code'] == 0
    assert '2/2' in response['msg']
    assert backend.database.song_exists(1) is False
    assert backend.database.song_exists(2) is False


def test_lib_del_batch_partial_failure(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.del', songs=[audio_file, 'ghost_song'])
    assert response['code'] == 0
    assert '1/2' in response['msg']
    assert len(response['failed']) == 1
    assert 'no such song in library' in response['failed'][0]['msg']
    assert backend.database.song_exists(1) is False


def test_lib_del_batch_all_failed(backend):
    response = _request(backend, 'lib.del', songs=['ghost_a', 'ghost_b'])
    assert response['code'] == 1
    assert '0/2' in response['msg']
    assert len(response['failed']) == 2


def test_lib_del_batch_empty(backend):
    response = _request(backend, 'lib.del', songs=[])
    assert response['code'] == 1
    assert 'empty list of songs' in response['msg']


def test_lib_alias_bind(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.alias.bind', song=audio_file, aliases=['favorite'])
    assert response['code'] == 0
    assert backend.database.get_song_via_alias('favorite') == 1


def test_lib_alias_bind_duplicate(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    _request(backend, 'lib.alias.bind', song=audio_file, aliases=['favorite'])
    response = _request(backend, 'lib.alias.bind', song=audio_file, aliases=['favorite'])
    assert response['code'] == 1
    assert 'already' in response['failed'][0]['msg']


def test_lib_alias_bind_missing_song(backend):
    response = _request(backend, 'lib.alias.bind', song='ghost_song', aliases=['favorite'])
    assert response['code'] == 1
    assert 'no such song in library' in response['msg']


def test_lib_alias_list(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    _request(backend, 'lib.alias.bind', song=audio_file, aliases=['favorite'])
    _request(backend, 'lib.alias.bind', song=audio_file, aliases=['workout'])
    response = _request(backend, 'lib.alias.list', song=audio_file)
    assert response['code'] == 0
    assert response['attachment'] == ['test_audio', 'favorite', 'workout']


def test_lib_alias_list_missing_song(backend):
    response = _request(backend, 'lib.alias.list', song='ghost_song')
    assert response['code'] == 1
    assert 'no such song in library' in response['msg']


def test_lib_alias_del(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    _request(backend, 'lib.alias.bind', song=audio_file, aliases=['favorite'])
    response = _request(backend, 'lib.alias.unbind', aliases=['favorite'])
    assert response['code'] == 0
    assert backend.database.get_song_via_alias('favorite') is SENTINELS.ALIAS_NOT_FOUND


def test_lib_alias_del_keeps_song(backend, audio_file):
    """Deleting an alias must not delete the song it was bound to."""
    _request(backend, 'lib.add', paths=[audio_file])
    _request(backend, 'lib.alias.bind', song=audio_file, aliases=['favorite'])
    _request(backend, 'lib.alias.unbind', aliases=['favorite'])
    assert backend.database.get_song_via_path(audio_file) == 1


def test_lib_alias_del_not_exist(backend):
    response = _request(backend, 'lib.alias.unbind', aliases=['ghost_alias'])
    assert response['code'] == 1
    assert 'alias not exist' in response['failed'][0]['msg']


def _create_playlist_with_song(backend, audio_file, playlist_name):
    """Seed a song + playlist + playlist membership for playlist tests."""
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    playlist_id = database.create_playlist(playlist_name)[0]
    database.add_song_to_playlist(playlist_id, song_id)
    return song_id, playlist_id


def _make_wav(path):
    """Write a short silent WAV file (mirrors the conftest audio_file fixture)."""
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(8000)
        f.writeframes(b'\x00\x00' * (8000 * 3))


def _open_playlist_with_songs(backend, paths, playlist_name):
    """Seed a playlist from existing files and open it."""
    database = backend.database
    playlist_id = database.create_playlist(playlist_name)[0]
    for path in paths:
        song_id, _ = database.add_song(path)
        database.add_song_to_playlist(playlist_id, song_id)
    response = _request(backend, 'open', song=playlist_name)
    assert response['code'] == 0


def test_lib_playlist_kick(backend, audio_file):
    song_id, playlist_id = _create_playlist_with_song(backend, audio_file, 'workout')
    response = _request(backend, 'lib.playlist.kick', songs=[audio_file], playlist='workout')
    assert response['code'] == 0
    assert backend.database.get_playlist_songs(playlist_id) == []
    assert backend.database.song_exists(song_id)


def test_lib_playlist_kick_by_alias(backend, audio_file):
    database = backend.database
    song_id, playlist_id = _create_playlist_with_song(backend, audio_file, 'workout')
    database.bind_alias(song_id, 'workout_song')
    response = _request(backend, 'lib.playlist.kick', songs=['workout_song'], playlist='workout')
    assert response['code'] == 0
    assert backend.database.get_playlist_songs(playlist_id) == []


def test_lib_playlist_kick_batch_multiple(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    _make_wav(tmp_path / 'b.wav')
    database = backend.database
    playlist_id = database.create_playlist('workout')[0]
    for path in (tmp_path / 'a.wav', tmp_path / 'b.wav'):
        song_id, _ = database.add_song(str(path))
        database.add_song_to_playlist(playlist_id, song_id)
    response = _request(backend, 'lib.playlist.kick', songs=[str(tmp_path / 'a.wav'), str(tmp_path / 'b.wav')], playlist='workout')
    assert response['code'] == 0
    assert '2/2' in response['msg']
    assert backend.database.get_playlist_songs(playlist_id) == []


def test_lib_playlist_kick_song_not_in_playlist(backend, audio_file):
    _create_playlist_with_song(backend, audio_file, 'workout')
    other_file = audio_file.replace('test_audio', 'test_other')
    song_id, _ = backend.database.add_song(other_file)
    response = _request(backend, 'lib.playlist.kick', songs=[other_file], playlist='workout')
    assert response['code'] == 1
    assert 'not in the playlist' in response['failed'][0]['msg']
    assert backend.database.song_exists(song_id)


def test_lib_playlist_kick_partial_failure(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    database = backend.database
    playlist_id = database.create_playlist('workout')[0]
    song_id, _ = database.add_song(str(tmp_path / 'a.wav'))
    database.add_song_to_playlist(playlist_id, song_id)
    response = _request(backend, 'lib.playlist.kick', songs=[str(tmp_path / 'a.wav'), 'ghost_song'], playlist='workout')
    assert response['code'] == 0
    assert '1/2' in response['msg']
    assert len(response['failed']) == 1
    assert 'no such song in library' in response['failed'][0]['msg']


def test_lib_playlist_kick_song_not_in_library(backend):
    _request(backend, 'lib.playlist.create', name='workout')
    response = _request(backend, 'lib.playlist.kick', songs=['ghost_song'], playlist='workout')
    assert response['code'] == 1
    assert 'no such song in library' in response['failed'][0]['msg']


def test_lib_playlist_kick_playlist_not_found(backend, audio_file):
    response = _request(backend, 'lib.playlist.kick', songs=[audio_file], playlist='ghost_playlist')
    assert response['code'] == 1
    assert 'no such playlist in library' in response['msg']


def _playlist_song_numbers(database, playlist_id):
    """Numbers ordered as the playlist is read, so 0..N-1 when nothing is wrong."""
    rows = database.execute('SELECT number FROM playlist_songs WHERE playlist_id = ? ORDER BY number, rowid', playlist_id).fetchall()
    numbers = []
    for row in rows:
        numbers.append(row['number'])
    return numbers


def _make_playlist_with_songs(backend, tmp_path, playlist_name='workout'):
    """Seed a playlist with three songs and return (paths, song_ids, playlist_id)."""
    database = backend.database
    paths = []
    song_ids = []
    for name in ('a.wav', 'b.wav', 'c.wav'):
        path = tmp_path / name
        _make_wav(path)
        paths.append(str(path))
        song_id, _ = database.add_song(str(path))
        song_ids.append(song_id)
    playlist_id = database.create_playlist(playlist_name)[0]
    for song_id in song_ids:
        database.add_song_to_playlist(playlist_id, song_id)
    return paths, song_ids, playlist_id


def test_lib_playlist_swap(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.swap', playlist='workout', song1=paths[0], song2=paths[2])
    assert response['code'] == 0
    assert 'swapped' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[2], song_ids[1], song_ids[0]]


def test_lib_playlist_swap_numbers_stay_dense(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    _request(backend, 'lib.playlist.swap', playlist='workout', song1=paths[0], song2=paths[2])
    assert _playlist_song_numbers(backend.database, playlist_id) == [0, 1, 2]


def test_lib_playlist_swap_by_alias(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    backend.database.bind_alias(song_ids[1], 'middle_song')
    response = _request(backend, 'lib.playlist.swap', playlist='workout', song1='middle_song', song2=paths[0])
    assert response['code'] == 0
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[1], song_ids[0], song_ids[2]]


def test_lib_playlist_swap_same_song_twice(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.swap', playlist='workout', song1=paths[1], song2=paths[1])
    assert response['code'] == 0
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_swap_song_not_in_playlist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    _make_wav(tmp_path / 'other.wav')
    other_id, _ = backend.database.add_song(str(tmp_path / 'other.wav'))
    response = _request(backend, 'lib.playlist.swap', playlist='workout', song1=str(tmp_path / 'other.wav'), song2=paths[0])
    assert response['code'] == 1
    assert 'not in playlist "workout"' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids
    assert backend.database.song_exists(other_id)


def test_lib_playlist_swap_song_not_exist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.swap', playlist='workout', song1=str(tmp_path / 'ghost.wav'), song2=paths[0])
    assert response['code'] == 1
    assert 'no such song in library' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_swap_playlist_not_exist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.swap', playlist='ghost', song1=paths[0], song2=paths[1])
    assert response['code'] == 1
    assert 'no such playlist in library' in response['msg']


def test_lib_playlist_swap_missing_key(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.swap', playlist='workout', song1=paths[0])
    assert response['code'] == 1
    assert 'song2' in response['msg']


def test_lib_playlist_swap_database_error(backend, tmp_path, monkeypatch):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    monkeypatch.setattr(backend.database, 'reorder_playlist', lambda playlist_id, song_ids: SENTINELS.DATABASE_ERROR)
    response = _request(backend, 'lib.playlist.swap', playlist='workout', song1=paths[0], song2=paths[1])
    assert response['code'] == 1
    assert 'database error' in response['msg']


def test_lib_playlist_move_to_first(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[2], position=1)
    assert response['code'] == 0
    assert 'is now the 1nd song' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[2], song_ids[0], song_ids[1]]


def test_lib_playlist_move_position_zero_is_first(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[2], position=0)
    assert response['code'] == 0
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[2], song_ids[0], song_ids[1]]


def test_lib_playlist_move_to_last(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[0], position=3)
    assert response['code'] == 0
    assert 'is now the 3nd song' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[1], song_ids[2], song_ids[0]]


def test_lib_playlist_move_negative_position(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[0], position=-1)
    assert response['code'] == 0
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[1], song_ids[2], song_ids[0]]


def test_lib_playlist_move_negative_position_from_start(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[1], position=-3)
    assert response['code'] == 0
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[1], song_ids[0], song_ids[2]]


def test_lib_playlist_move_numbers_stay_dense(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    _request(backend, 'lib.playlist.move', playlist='workout', song=paths[2], position=1)
    assert _playlist_song_numbers(backend.database, playlist_id) == [0, 1, 2]


def test_lib_playlist_move_by_alias(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    backend.database.bind_alias(song_ids[1], 'middle_song')
    response = _request(backend, 'lib.playlist.move', playlist='workout', song='middle_song', position=1)
    assert response['code'] == 0
    assert _playlist_song_ids(backend.database, playlist_id) == [song_ids[1], song_ids[0], song_ids[2]]


def test_lib_playlist_move_position_out_of_bound(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[0], position=4)
    assert response['code'] == 1
    assert 'out of bound' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_move_negative_position_out_of_bound(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[0], position=-4)
    assert response['code'] == 1
    assert 'out of bound' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_move_song_not_in_playlist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    _make_wav(tmp_path / 'other.wav')
    other_id, _ = backend.database.add_song(str(tmp_path / 'other.wav'))
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=str(tmp_path / 'other.wav'), position=1)
    assert response['code'] == 1
    assert 'not in playlist "workout"' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids
    assert backend.database.song_exists(other_id)


def test_lib_playlist_move_song_not_exist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=str(tmp_path / 'ghost.wav'), position=1)
    assert response['code'] == 1
    assert 'no such song in library' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_move_playlist_not_exist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='ghost', song=paths[0], position=1)
    assert response['code'] == 1
    assert 'no such playlist in library' in response['msg']


def test_lib_playlist_move_missing_key(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[0])
    assert response['code'] == 1
    assert 'position' in response['msg']


def test_lib_playlist_move_invalid_position(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[0], position='first')
    assert response['code'] == 1
    assert 'position' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_move_database_error(backend, tmp_path, monkeypatch):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    monkeypatch.setattr(backend.database, 'reorder_playlist', lambda playlist_id, song_ids: SENTINELS.DATABASE_ERROR)
    response = _request(backend, 'lib.playlist.move', playlist='workout', song=paths[0], position=1)
    assert response['code'] == 1
    assert 'database error' in response['msg']


def test_lib_playlist_reorder(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    target = [song_ids[2], song_ids[1], song_ids[0]]
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=target)
    assert response['code'] == 0
    assert 'reordered' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == target


def test_lib_playlist_reorder_numbers_stay_dense(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=[song_ids[1], song_ids[2], song_ids[0]])
    assert _playlist_song_numbers(backend.database, playlist_id) == [0, 1, 2]


def test_lib_playlist_reorder_song_ids_mismatch(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=[song_ids[2], song_ids[1]])
    assert response['code'] == 1
    assert 'do not match' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_reorder_duplicate_song_id(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=[song_ids[0], song_ids[0], song_ids[1]])
    assert response['code'] == 1
    assert 'do not match' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_reorder_song_id_not_in_library(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=[song_ids[0], song_ids[1], 999])
    assert response['code'] == 1
    assert 'do not match' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_reorder_empty_playlist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    _request(backend, 'lib.playlist.kick', songs=paths, playlist='workout')
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=[])
    assert response['code'] == 0
    assert _playlist_song_ids(backend.database, playlist_id) == []


def test_lib_playlist_reorder_playlist_not_exist(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.reorder', playlist='ghost', song_ids=song_ids)
    assert response['code'] == 1
    assert 'no such playlist in library' in response['msg']


def test_lib_playlist_reorder_missing_key(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.reorder', playlist='workout')
    assert response['code'] == 1
    assert 'song_ids' in response['msg']


def test_lib_playlist_reorder_invalid_song_id(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=[song_ids[0], 'not_a_number', song_ids[2]])
    assert response['code'] == 1
    assert 'song_ids' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_reorder_song_ids_not_a_list(backend, tmp_path):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=song_ids[0])
    assert response['code'] == 1
    assert 'song_ids' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == song_ids


def test_lib_playlist_reorder_database_error(backend, tmp_path, monkeypatch):
    paths, song_ids, playlist_id = _make_playlist_with_songs(backend, tmp_path)
    monkeypatch.setattr(backend.database, 'reorder_playlist', lambda playlist_id, song_ids: SENTINELS.DATABASE_ERROR)
    response = _request(backend, 'lib.playlist.reorder', playlist='workout', song_ids=[song_ids[2], song_ids[1], song_ids[0]])
    assert response['code'] == 1
    assert 'database error' in response['msg']


def test_lib_playlist_add(backend, audio_file):
    song_id, playlist_id = _create_playlist_with_song(backend, audio_file, 'workout')
    # seed another song that is NOT in the playlist yet
    other_file = audio_file.replace('test_audio', 'test_other')
    other_id, _ = backend.database.add_song(other_file)
    response = _request(backend, 'lib.playlist.add', songs=[other_file], playlist='workout')
    assert response['code'] == 0
    assert '1/1' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == [song_id, other_id]


def test_lib_playlist_add_batch_multiple(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    _make_wav(tmp_path / 'b.wav')
    database = backend.database
    playlist_id = database.create_playlist('workout')[0]
    for path in (tmp_path / 'a.wav', tmp_path / 'b.wav'):
        database.add_song(str(path))
    response = _request(backend, 'lib.playlist.add', songs=[str(tmp_path / 'a.wav'), str(tmp_path / 'b.wav')], playlist='workout')
    assert response['code'] == 0
    assert '2/2' in response['msg']
    assert len(backend.database.get_playlist_songs(playlist_id)) == 2


def test_lib_playlist_add_by_alias(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    playlist_id = database.create_playlist('workout')[0]
    database.bind_alias(song_id, 'workout_song')
    response = _request(backend, 'lib.playlist.add', songs=['workout_song'], playlist='workout')
    assert response['code'] == 0
    assert '1/1' in response['msg']
    assert _playlist_song_ids(backend.database, playlist_id) == [song_id]


def test_lib_playlist_add_partial_failure(backend, tmp_path):
    _make_wav(tmp_path / 'a.wav')
    database = backend.database
    playlist_id = database.create_playlist('workout')[0]
    database.add_song(str(tmp_path / 'a.wav'))
    response = _request(backend, 'lib.playlist.add', songs=[str(tmp_path / 'a.wav'), 'ghost_song'], playlist='workout')
    assert response['code'] == 0
    assert '1/2' in response['msg']
    assert len(response['failed']) == 1
    assert 'no such song in library' in response['failed'][0]['msg']
    assert len(backend.database.get_playlist_songs(playlist_id)) == 1


def test_lib_playlist_add_all_failed(backend):
    _request(backend, 'lib.playlist.create', name='workout')
    response = _request(backend, 'lib.playlist.add', songs=['ghost_one', 'ghost_two'], playlist='workout')
    assert response['code'] == 1
    assert '0/2' in response['msg']
    assert len(response['failed']) == 2


def test_lib_playlist_add_duplicate(backend, audio_file):
    _create_playlist_with_song(backend, audio_file, 'workout')
    response = _request(backend, 'lib.playlist.add', songs=[audio_file], playlist='workout')
    assert response['code'] == 1
    assert 'already in the playlist' in response['failed'][0]['msg']


def test_lib_playlist_add_empty(backend):
    _request(backend, 'lib.playlist.create', name='workout')
    response = _request(backend, 'lib.playlist.add', songs=[], playlist='workout')
    assert response['code'] == 1
    assert 'empty list of songs' in response['msg']


def test_lib_playlist_add_playlist_not_found(backend, audio_file):
    response = _request(backend, 'lib.playlist.add', songs=[audio_file], playlist='ghost_playlist')
    assert response['code'] == 1
    assert 'no such playlist in library' in response['msg']


def test_lib_playlist_del(backend):
    _request(backend, 'lib.playlist.create', name='workout')
    response = _request(backend, 'lib.playlist.del', playlist='workout')
    assert response['code'] == 0
    assert backend.database.get_playlist_via_name('workout') is SENTINELS.PLAYLIST_NOT_FOUND


def test_lib_playlist_del_cascades_membership(backend, audio_file):
    _create_playlist_with_song(backend, audio_file, 'workout')
    response = _request(backend, 'lib.playlist.del', playlist='workout')
    assert response['code'] == 0
    assert backend.database.get_all_playlists() == []


def test_lib_playlist_del_playlist_not_found(backend):
    response = _request(backend, 'lib.playlist.del', playlist='ghost_playlist')
    assert response['code'] == 1
    assert 'no such playlist in library' in response['msg']


def test_lib_playlist_del_missing_key(backend):
    response = _request(backend, 'lib.playlist.del')
    assert response['code'] == 1
    assert 'playlist' in response['msg']


def test_replay_before_open(backend):
    response = _request(backend, 'replay')
    assert response['code'] == 1
    assert 'neither playing nor paused' in response['msg']


def test_replay_after_open(backend, audio_file):
    response = _request(backend, 'open', song=audio_file)
    assert response['code'] == 0
    response = _request(backend, 'replay')
    assert response['code'] == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == audio_file


def test_replay_clears_memorized_pos(backend, audio_file):
    database = backend.database
    response = _request(backend, 'open', song=audio_file)
    assert response['code'] == 0
    database.set_pos(audio_file, 1000)
    assert database.get_pos(audio_file) == 1000

    response = _request(backend, 'replay')
    assert response['code'] == 0
    assert database.get_pos(audio_file) is SENTINELS.POS_NOT_FOUND


def test_search_missing_keyword(backend):
    response = _request(backend, 'lib.search')
    assert response['code'] == 1
    assert 'keyword' in response['msg']


def test_search_no_results(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.search', keyword=['nonexistent'])
    assert response['code'] == 0
    assert response['attachment'] == []


def test_search_by_name(backend, audio_file):
    database = backend.database
    _request(backend, 'lib.add', paths=[audio_file])
    song_id = database.get_all_song_info()[0]['id']
    database.set_song_meta(song_id, 'name', 'My Awesome Song')
    response = _request(backend, 'lib.search', keyword=['awesome'])
    assert response['code'] == 0
    assert len(response['attachment']) == 1
    assert response['attachment'][0]['name'] == 'My Awesome Song'


def test_search_by_alias(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file], aliases=['MyAlias'])
    response = _request(backend, 'lib.search', keyword=['alias'])
    assert response['code'] == 0
    assert len(response['attachment']) == 1


def test_search_case_insensitive(backend, audio_file):
    database = backend.database
    _request(backend, 'lib.add', paths=[audio_file])
    song_id = database.get_all_song_info()[0]['id']
    database.set_song_meta(song_id, 'artist', 'Metallica')
    response = _request(backend, 'lib.search', keyword=['METALLICA'])
    assert response['code'] == 0
    assert len(response['attachment']) == 1


def test_search_partial_match(backend, audio_file):
    database = backend.database
    _request(backend, 'lib.add', paths=[audio_file])
    song_id = database.get_all_song_info()[0]['id']
    database.set_song_meta(song_id, 'name', 'Hello World')
    response = _request(backend, 'lib.search', keyword=['wor'])
    assert response['code'] == 0
    assert len(response['attachment']) == 1


def test_search_multi_keyword_and(backend, audio_file):
    database = backend.database
    _request(backend, 'lib.add', paths=[audio_file])
    song_id = database.get_all_song_info()[0]['id']
    database.set_song_meta(song_id, 'name', 'My Awesome Song')
    database.set_song_meta(song_id, 'artist', 'Metallica')

    # AND(默认):两个 keyword 都命中 → 匹配
    response = _request(backend, 'lib.search', keyword=['awesome', 'metallica'])
    assert response['code'] == 0
    assert len(response['attachment']) == 1

    # AND:一个不命中 → 不匹配
    response = _request(backend, 'lib.search', keyword=['awesome', 'ghost'])
    assert response['code'] == 0
    assert response['attachment'] == []


def test_search_multi_keyword_or(backend, audio_file):
    database = backend.database
    _request(backend, 'lib.add', paths=[audio_file])
    song_id = database.get_all_song_info()[0]['id']
    database.set_song_meta(song_id, 'name', 'My Awesome Song')

    # OR:任一 keyword 命中 → 匹配
    response = _request(backend, 'lib.search', keyword=['awesome', 'ghost'], **{'or': True})
    assert response['code'] == 0
    assert len(response['attachment']) == 1

    # OR:全不命中 → 不匹配
    response = _request(backend, 'lib.search', keyword=['ghost1', 'ghost2'], **{'or': True})
    assert response['code'] == 0
    assert response['attachment'] == []



def test_jump_missing_progress(backend):
    response = _request(backend, 'jump')
    assert response['code'] == 1
    assert 'progress' in response['msg']


def test_jump_before_open(backend):
    response = _request(backend, 'jump', progress=50)
    assert response['code'] == 1
    assert 'neither playing nor paused' in response['msg']


def test_jump_lower_than_zero(backend):
    response = _request(backend, 'jump', progress=-1)
    assert response['code'] == 1
    assert 'lower than 0' in response['msg']


def test_jump_higher_than_100(backend):
    response = _request(backend, 'jump', progress=101)
    assert response['code'] == 1
    assert 'higher than 100' in response['msg']


def test_jump_success(backend, audio_file):
    _request(backend, 'open', song=audio_file)
    response = _request(backend, 'jump', progress=50)
    assert response['code'] == 0
    assert 'jumped to' in response['msg']
    status = _request(backend, 'status')
    assert status['attachment']['time'] >= 1500


def test_jump_ended_state_not_crash(backend, monkeypatch):
    """Ended/Stopped state with a known length must return a proper error, not dispatch_failed."""
    monkeypatch.setattr(backend.playback.engine, 'get_progress', lambda: (3000, 3000))
    response = _request(backend, 'jump', progress=50)
    assert response['code'] == 1
    assert 'neither playing nor paused' in response['msg']


def test_seek_missing_time(backend):
    response = _request(backend, 'seek')
    assert response['code'] == 1
    assert 'time' in response['msg']


def test_seek_invalid_time(backend):
    response = _request(backend, 'seek', time='abc')
    assert response['code'] == 1
    assert 'invalid time' in response['msg']


def test_seek_invalid_relative_time(backend):
    response = _request(backend, 'seek', time='+abc')
    assert response['code'] == 1
    assert 'invalid' in response['msg']


def test_seek_relative_before_open(backend):
    response = _request(backend, 'seek', time='+1')
    assert response['code'] == 1
    assert 'neither playing nor paused' in response['msg']


def test_seek_relative_forward(backend, audio_file):
    _request(backend, 'open', song=audio_file)
    response = _request(backend, 'seek', time='+1')
    assert response['code'] == 0
    assert 'jumped to' in response['msg']


def test_seek_relative_backward(backend, audio_file):
    _request(backend, 'open', song=audio_file)
    _request(backend, 'seek', time='+1')
    response = _request(backend, 'seek', time='-1')
    assert response['code'] == 0
    assert 'jumped to' in response['msg']


def test_seek_invalid_time_too_many_parts(backend):
    response = _request(backend, 'seek', time='1:2:3:4')
    assert response['code'] == 1
    assert 'invalid time' in response['msg']


def test_seek_before_open(backend):
    response = _request(backend, 'seek', time='1')
    assert response['code'] == 1
    assert 'neither playing nor paused' in response['msg']


def test_seek_success(backend, audio_file):
    _request(backend, 'open', song=audio_file)
    response = _request(backend, 'seek', time='00:01')
    assert response['code'] == 0
    assert 'jumped to' in response['msg']
    status = _request(backend, 'status')
    assert status['attachment']['time'] >= 500


def test_seek_pos_too_late(backend, audio_file):
    _request(backend, 'open', song=audio_file)
    response = _request(backend, 'seek', time='1:00')
    assert response['code'] == 1
    assert 'later than the end' in response['msg']


def test_seek_hours_parsed_correctly(backend):
    """1:02:03 must resolve to 1h2m3s (the 3600000 fix), verified without a player."""
    from src.utils.time_ import parse_time, format_time
    assert format_time(parse_time('1:02:03')) == '01:02:03'


def test_scan_missing_dir(backend):
    response = _request(backend, 'lib.scan')
    assert response['code'] == 1
    assert 'dir' in response['msg']


def test_scan_invalid_directory(backend, tmp_path):
    response = _request(backend, 'lib.scan', dir=str(tmp_path / 'not_a_dir'))
    assert response['code'] == 1
    assert 'not a valid directory' in response['msg']


def test_scan_dry_run(backend, tmp_path):
    _make_wav(tmp_path / 'test_a.wav')
    _make_wav(tmp_path / 'test_b.wav')
    response = _request(backend, 'lib.scan', dir=str(tmp_path), dry_run=True)
    assert response['code'] == 0
    assert len(response['attachment']) == 2
    assert response['attachment'][0].endswith('test_a.wav')
    # dry run must not add anything to the library
    assert _request(backend, 'lib.list')['attachment'] == []


def test_scan_success(backend, tmp_path):
    _make_wav(tmp_path / 'test_a.wav')
    _make_wav(tmp_path / 'test_b.wav')
    response = _request(backend, 'lib.scan', dir=str(tmp_path))
    assert response['code'] == 0
    assert '2/2' in response['msg']
    assert response['failed'] == []
    assert len(_request(backend, 'lib.list')['attachment']) == 2


def test_scan_partial_failure(backend, tmp_path):
    _make_wav(tmp_path / 'test_a.wav')
    _make_wav(tmp_path / 'test_b.wav')
    _request(backend, 'lib.add', paths=[str(tmp_path / 'test_a.wav')])
    response = _request(backend, 'lib.scan', dir=str(tmp_path))
    assert response['code'] == 0
    assert '1/2' in response['msg']
    assert len(response['failed']) == 1
    assert 'already exists' in response['failed'][0]['msg']
    assert len(_request(backend, 'lib.list')['attachment']) == 2


def test_scan_recurse(backend, tmp_path):
    sub = tmp_path / 'sub'
    sub.mkdir()
    _make_wav(sub / 'test_c.wav')
    response = _request(backend, 'lib.scan', dir=str(tmp_path))
    assert response['code'] == 0
    assert 'no supported audio file found' in response['msg']

    response = _request(backend, 'lib.scan', dir=str(tmp_path), recurse=True)
    assert response['code'] == 0
    assert '1/1' in response['msg']
    assert len(_request(backend, 'lib.list')['attachment']) == 1


def test_scan_with_playlist(backend, tmp_path):
    _make_wav(tmp_path / 'test_a.wav')
    database = backend.database
    database.create_playlist('scanlist')
    response = _request(backend, 'lib.scan', dir=str(tmp_path), playlist='scanlist')
    assert response['code'] == 0
    assert 'added 1 song(s) to playlist' in response['msg']
    playlist_id = database.get_playlist_via_name('scanlist')
    assert len(database.get_playlist_songs(playlist_id)) == 1


def test_lib_info_single_song(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    response = _request(backend, 'lib.info', songs=[audio_file])
    assert response['code'] == 0
    assert 'got information of [1/1] songs' in response['msg']
    assert len(response['attachment']) == 1
    assert response['attachment'][0]['id'] == song_id
    assert response['attachment'][0]['path'] == audio_file
    assert response['failed'] == []


def test_lib_info_multiple_songs(backend, audio_file, tmp_path):
    second = str(tmp_path / 'test_b.wav')
    _make_wav(second)
    database = backend.database
    database.add_song(audio_file)
    database.add_song(second)

    response = _request(backend, 'lib.info', songs=[audio_file, second])
    assert response['code'] == 0
    assert 'got information of [2/2] songs' in response['msg']
    assert len(response['attachment']) == 2


def test_lib_info_by_alias(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'my_song')
    response = _request(backend, 'lib.info', songs=['my_song'])
    assert response['code'] == 0
    assert response['attachment'][0]['id'] == song_id


def test_lib_info_partial_failure(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    response = _request(backend, 'lib.info', songs=[audio_file, 'ghost_song'])
    # 至少一个成功 → code 0,失败的进 failed
    assert response['code'] == 0
    assert 'got information of [1/2] songs' in response['msg']
    assert len(response['attachment']) == 1
    assert len(response['failed']) == 1
    assert 'no such song in library' in response['failed'][0]['msg']


def test_lib_info_all_failed(backend, audio_file):
    response = _request(backend, 'lib.info', songs=['ghost_a', 'ghost_b'])
    # 全部失败 → code 1
    assert response['code'] == 1
    assert 'got information of [0/2] songs' in response['msg']
    assert response['attachment'] == {}
    assert len(response['failed']) == 2


def test_lib_info_missing_songs_key(backend, audio_file):
    backend.database.add_song(audio_file)
    response = _request(backend, 'lib.info')
    assert response['code'] == 1
    assert 'songs' in response['msg']


def test_lib_info_songs_must_be_list(backend, audio_file):
    backend.database.add_song(audio_file)
    # IterType(str): a bare string is not a list/tuple -> InvalidKeyType
    response = _request(backend, 'lib.info', songs=audio_file)
    assert response['code'] == 1
    assert 'not a list or tuple' in response['msg']


def test_lib_info_songs_element_type(backend, audio_file):
    backend.database.add_song(audio_file)
    # the callable-validator model coerces elements instead of type-checking them,
    # so an int element is looked up as the string "123"
    response = _request(backend, 'lib.info', songs=[123])
    assert response['code'] == 1
    assert '[0/1]' in response['msg']


def test_lib_info_songs_not_a_list(backend):
    response = _request(backend, 'lib.info', songs=123)
    assert response['code'] == 1
    assert 'not a list or tuple' in response['msg']


def test_lib_info_with_aliases(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'my_song')
    response = _request(backend, 'lib.info', songs=[audio_file], show_aliases=True)
    assert response['code'] == 0
    assert response['attachment'][0]['aliases'] == ['my_song']


def test_lib_info_with_playlists(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    playlist_id = database.create_playlist('work')[0]
    database.add_song_to_playlist(playlist_id, song_id)
    response = _request(backend, 'lib.info', songs=[audio_file], show_playlists=True)
    assert response['code'] == 0
    assert response['attachment'][0]['playlists'] == ['work']


def test_lib_info_force_id(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    response = _request(backend, 'lib.info', songs=[str(song_id)], force_id=True)
    assert response['code'] == 0
    assert 'got information of [1/1] songs' in response['msg']
    assert response['attachment'][0]['id'] == song_id
    assert response['failed'] == []


def test_lib_info_force_id_not_found(backend, audio_file):
    database = backend.database
    database.add_song(audio_file)
    # ID 不存在 → failed
    response = _request(backend, 'lib.info', songs=['999'], force_id=True)
    assert response['code'] == 1
    assert 'got information of [0/1] songs' in response['msg']
    assert response['attachment'] == {}
    assert len(response['failed']) == 1
    assert 'no such song in library' in response['failed'][0]['msg']


def test_lib_info_force_id_non_decimal(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'my_song')
    # force_id 模式不做 alias/路径解析,非数字输入直接失败
    response = _request(backend, 'lib.info', songs=['my_song'], force_id=True)
    assert response['code'] == 1
    assert len(response['failed']) == 1
    assert 'no such song in library' in response['failed'][0]['msg']


def test_lib_info_force_id_ignores_cwd(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    # force_id 按 ID 直查,不需要 cwd(dash 的 lib.info 请求不带 cwd)
    response = _request(backend, 'lib.info', songs=[str(song_id)], force_id=True, cwd=None)
    assert response['code'] == 0
    assert response['attachment'][0]['id'] == song_id
    assert response['failed'] == []


def test_lib_prune_dry_run_empty(backend, audio_file):
    _request(backend, 'lib.add', paths=[audio_file])
    response = _request(backend, 'lib.prune', dry_run=True)
    assert response['code'] == 0
    assert response['attachment'] == []


def test_lib_prune_dry_run_finds_missing(backend, tmp_path):
    database = backend.database
    ghost = str(tmp_path / 'ghost.wav')
    database.add_song(ghost)
    response = _request(backend, 'lib.prune', dry_run=True)
    assert response['code'] == 0
    assert len(response['attachment']) == 1
    assert response['attachment'][0]['path'] == ghost
    # dry run must not delete anything
    assert database.song_exists(1)


def test_lib_prune_removes_missing(backend, tmp_path):
    database = backend.database
    ghost = str(tmp_path / 'ghost.wav')
    ghost_id, _ = database.add_song(ghost)
    real = str(tmp_path / 'real.wav')
    _make_wav(real)
    real_id, _ = database.add_song(real)
    response = _request(backend, 'lib.prune')
    assert response['code'] == 0
    assert database.song_exists(ghost_id) is False
    assert database.song_exists(real_id) is True


def test_lib_prune_removes_from_current_playlist(backend, audio_file, tmp_path):
    """A song in the current playlist whose file disappears later must be removed from both DB and playlist."""
    second = str(tmp_path / 'test_b.wav')
    _make_wav(second)
    _open_playlist_with_songs(backend, [audio_file, second], 'pair')
    assert backend.playback.current_song_info is not None
    assert len(backend.playback.current_song_info) == 2

    os.remove(second)  # file goes missing after the playlist was opened
    response = _request(backend, 'lib.prune')
    assert response['code'] == 0
    assert len(backend.database.get_all_song_info()) == 1
    paths = [s['path'] for s in backend.playback.current_song_info]
    assert second not in paths
    assert audio_file in paths


def test_shuffle_toggle_on_off(backend):
    response = _request(backend, 'shuffle')
    assert response['code'] == 0
    assert 'on' in response['msg']
    assert backend.playback.shuffle is True

    response = _request(backend, 'shuffle')
    assert response['code'] == 0
    assert 'off' in response['msg']
    assert backend.playback.shuffle is False


def test_shuffle_next_uses_order_and_reshuffles(backend, audio_file, tmp_path, monkeypatch):
    _, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.shuffle = True
    backend.playback.shuffle_order = [1, 0]  # current (0) sits at the tail: next wraps and reshuffles

    reshuffled = []
    from src.backend.handlers.playback import helpers
    monkeypatch.setattr(helpers.random, 'shuffle', lambda lst: reshuffled.append(list(lst)))

    response = _request(backend, 'next')
    assert response['code'] == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second
    assert len(reshuffled) == 1  # tail wrap triggers reshuffle


def test_shuffle_prev_wraps_without_reshuffle(backend, audio_file, tmp_path, monkeypatch):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.shuffle = True
    backend.playback.shuffle_order = [1, 0]
    backend.playback.current_song_num = 1  # second song, at position 0 of the order

    reshuffled = []
    from src.backend.handlers.playback import helpers
    monkeypatch.setattr(helpers.random, 'shuffle', lambda lst: reshuffled.append(list(lst)))

    response = _request(backend, 'prev')
    assert response['code'] == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first  # wraps to tail without reshuffle
    assert len(reshuffled) == 0


def test_shuffle_next_without_songs(backend):
    backend.playback.shuffle = True
    response = _request(backend, 'next')
    assert response['code'] == 1
    assert 'no songs are being played' in response['msg']


def test_shuffle_order_rebuilt_on_open(backend, audio_file, tmp_path, monkeypatch):
    backend.playback.shuffle = True
    reshuffled = []
    monkeypatch.setattr('src.backend.playback.core.random.shuffle', lambda lst: reshuffled.append(list(lst)))
    _open_two_song_playlist(backend, audio_file, tmp_path)
    assert len(backend.playback.shuffle_order) == 2


def test_loop_toggle_on_off(backend):
    response = _request(backend, 'loop')
    assert response['code'] == 0
    assert 'on' in response['msg']
    assert backend.playback.loop is True

    response = _request(backend, 'loop')
    assert response['code'] == 0
    assert 'off' in response['msg']
    assert backend.playback.loop is False


def test_loop_next_on_end_replays_current(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.loop = True

    response = _request(backend, 'next', on_end=True)
    assert response['code'] == 0
    assert 'replayed' in response['msg']
    assert backend.playback.current_song_num == 0  # stays on the same song
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first


def test_loop_next_on_end_without_loop_advances(backend, audio_file, tmp_path):
    _, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    response = _request(backend, 'next', on_end=True)
    assert response['code'] == 0
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_loop_manual_next_still_advances(backend, audio_file, tmp_path):
    _, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.loop = True

    response = _request(backend, 'next')
    assert response['code'] == 0
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_loop_prev_on_end_replays_current(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.loop = True

    response = _request(backend, 'prev', on_end=True)
    assert response['code'] == 0
    assert 'replayed' in response['msg']
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first


def test_reverse_toggle_on_off(backend):
    response = _request(backend, 'reverse')
    assert response['code'] == 0
    assert 'on' in response['msg']
    assert backend.playback.reverse is True

    response = _request(backend, 'reverse')
    assert response['code'] == 0
    assert 'off' in response['msg']
    assert backend.playback.reverse is False


def test_reverse_reported_in_status(backend):
    status = _request(backend, 'status')
    assert status['attachment']['reverse'] is False

    _request(backend, 'reverse')
    status = _request(backend, 'status')
    assert status['attachment']['reverse'] is True


def test_reverse_on_end_switches_to_previous(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    _request(backend, 'next')
    assert backend.playback.current_song_num == 1
    backend.playback.reverse = True

    request, response = _run_buffered_request(backend)
    assert request['action'] == 'prev'
    assert response['code'] == 0
    assert 'previous' in response['msg']
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first


def test_reverse_on_end_wraps_at_first_song(backend, audio_file, tmp_path):
    _, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.reverse = True

    request, response = _run_buffered_request(backend)
    assert request['action'] == 'prev'
    assert response['code'] == 0
    assert backend.playback.current_song_num == 1  # wraps to the last song
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_reverse_does_not_affect_manual_next(backend, audio_file, tmp_path):
    _, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.reverse = True

    response = _request(backend, 'next')
    assert response['code'] == 0
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_reverse_on_end_with_loop_replays_current(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    backend.playback.reverse = True
    backend.playback.loop = True

    request, response = _run_buffered_request(backend)
    assert request['action'] == 'prev'
    assert response['code'] == 0
    assert 'replayed' in response['msg']
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == first


def test_playback_on_end_buffers_next(backend):
    backend.playback.on_end()
    request, connection = backend.dispatch_buffer.get()
    assert request['action'] == 'next'
    assert request['on_end'] is True
    assert request['source'] == 'player'
    assert connection is None


def test_playback_on_end_buffers_prev_when_reversed(backend):
    backend.playback.reverse = True
    backend.playback.on_end()
    request, connection = backend.dispatch_buffer.get()
    assert request['action'] == 'prev'
    assert request['on_end'] is True
    assert request['source'] == 'player'
    assert connection is None


def test_prev_on_end_deletes_memorized_pos(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    database = backend.database
    database.set_pos(first, 1000)

    response = _request(backend, 'prev', on_end=True)
    assert response['code'] == 0
    assert database.get_pos(first) is SENTINELS.POS_NOT_FOUND


def test_manual_prev_keeps_memorized_pos(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    database = backend.database
    database.set_pos(first, 1000)

    response = _request(backend, 'prev')
    assert response['code'] == 0
    assert database.get_pos(first) == 1000


def test_invalid_key_type(backend):
    response = _request(backend, 'switch', number='abc')
    assert response['code'] == 1
    assert 'invalid value "abc" of key "number"' in response['msg']


def test_optional_key_none_accepted(backend, audio_file):
    response = _request(backend, 'lib.add', paths=[audio_file])
    assert response['code'] == 0


def test_lib_meta_set_name(backend, audio_file):
    song_id, _ = backend.database.add_song(audio_file)
    response = _request(backend, 'lib.meta.set', song=audio_file, name='Foo')
    assert response['code'] == 0
    assert backend.database.get_song_meta(song_id, 'name') == 'Foo'


def test_lib_meta_set_multiple_fields(backend, audio_file):
    song_id, _ = backend.database.add_song(audio_file)
    response = _request(backend, 'lib.meta.set', song=audio_file,
                        name='Foo', artist='Bar', album='Baz')
    assert response['code'] == 0
    assert backend.database.get_song_meta(song_id, 'name') == 'Foo'
    assert backend.database.get_song_meta(song_id, 'artist') == 'Bar'
    assert backend.database.get_song_meta(song_id, 'album') == 'Baz'


def test_lib_meta_set_by_alias(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.bind_alias(song_id, 'my_song')
    response = _request(backend, 'lib.meta.set', song='my_song', artist='Bar')
    assert response['code'] == 0
    assert database.get_song_meta(song_id, 'artist') == 'Bar'


def test_lib_meta_set_clear(backend, audio_file):
    song_id, _ = backend.database.add_song(audio_file)
    backend.database.set_song_meta(song_id, 'name', 'Foo')
    assert backend.database.get_song_meta(song_id, 'name') == 'Foo'

    response = _request(backend, 'lib.meta.set', song=audio_file, name='')
    assert response['code'] == 0
    assert backend.database.get_song_meta(song_id, 'name') is None


def test_lib_meta_set_no_metadata_given(backend, audio_file):
    backend.database.add_song(audio_file)
    response = _request(backend, 'lib.meta.set', song=audio_file)
    assert response['code'] == 1
    assert 'no metadata was provided' in response['msg']


def test_lib_meta_set_song_not_in_library(backend):
    response = _request(backend, 'lib.meta.set', song='ghost_song', name='Foo')
    assert response['code'] == 1
    assert 'no such song in library' in response['msg']


def test_lib_meta_set_missing_song_key(backend):
    response = _request(backend, 'lib.meta.set', name='Foo')
    assert response['code'] == 1
    assert 'song' in response['msg']


def test_play_all_empty_library(backend):
    response = _request(backend, 'play-all')
    assert response['code'] == 1
    assert 'no song in library' in response['msg']


def test_play_all_two_songs(backend, audio_file, tmp_path):
    second = str(tmp_path / 'test_b.wav')
    _make_wav(second)
    backend.database.add_song(audio_file)
    backend.database.add_song(second)

    response = _request(backend, 'play-all')
    assert response['code'] == 0
    assert backend.playback.current_playlist is SENTINELS.PLAY_ALL
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == audio_file


def test_play_all_restores_last_num(backend, audio_file, tmp_path):
    first = audio_file
    second = str(tmp_path / 'test_b.wav')
    _make_wav(second)
    backend.database.add_song(first)
    backend.database.add_song(second)

    _request(backend, 'play-all')
    _request(backend, 'switch', number=2)
    assert backend.playback.current_song_num == 1

    response = _request(backend, 'play-all')
    assert response['code'] == 0
    assert 'last played number detected' in response['msg']
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_play_all_restores_zero_when_never_played(backend, audio_file, tmp_path):
    second = str(tmp_path / 'test_b.wav')
    _make_wav(second)
    backend.database.add_song(audio_file)
    backend.database.add_song(second)

    response = _request(backend, 'play-all')
    assert response['code'] == 0
    # 从未播过 → 从 0 开始,不应有 'last played number detected'
    assert 'last played number detected' not in response['msg']
    assert backend.playback.current_song_num == 0


def test_load_last_no_last_song(backend):
    response = _request(backend, 'load_last')
    assert response['code'] == 1
    assert 'no last song' in response['msg']


def test_load_last_opens_last_song(backend, audio_file):
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.set_setting('last_is_all', '0')
    database.set_setting('last_type', 'song')
    database.set_setting('last_reference', song_id)

    response = _request(backend, 'load_last')
    assert response['code'] == 0
    assert backend.playback.current_song_num == 0
    status = _request(backend, 'status')
    assert status['attachment']['path'] == audio_file


def test_load_last_play_all_mode(backend, audio_file, tmp_path):
    second = str(tmp_path / 'test_b.wav')
    _make_wav(second)
    backend.database.add_song(audio_file)
    backend.database.add_song(second)

    backend.database.set_setting('last_is_all', '1')

    response = _request(backend, 'load_last')
    assert response['code'] == 0
    assert backend.playback.current_playlist is SENTINELS.PLAY_ALL


def test_load_last_ignores_num_setting(backend, audio_file):
    # 旧的全局 last_num setting 不应再影响 load_last(已被 playlist last_num 取代)
    database = backend.database
    song_id, _ = database.add_song(audio_file)
    database.set_setting('last_is_all', '0')
    database.set_setting('last_type', 'song')
    database.set_setting('last_reference', song_id)
    database.set_setting('last_num', 999)  # 毒数据:若被读取会导致越界

    response = _request(backend, 'load_last')
    assert response['code'] == 0
    assert backend.playback.current_song_num == 0


def test_load_last_opens_last_playlist(backend, audio_file, tmp_path):
    """The persisted playlist reference round-trips through load_last.

    last_reference comes back as a string from the settings table, so this also
    covers open_type being handed an id that is not the int the resolver produced.
    """
    first, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    playlist_id = backend.database.get_playlist_via_name('pair')
    assert backend.database.get_setting('last_type') == 'playlist'
    assert int(backend.database.get_setting('last_reference')) == playlist_id

    response = _request(backend, 'load_last')
    assert response['code'] == 0
    status = _request(backend, 'status')
    assert status['attachment']['playlist_len'] == 2
    assert status['attachment']['path'] in (first, second)


def test_open_playlist_restores_last_num(backend, audio_file, tmp_path):
    first, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    assert backend.playback.current_song_num == 0

    # 切到第二首 → last_num 应写入该 playlist
    _request(backend, 'switch', number=2)
    assert backend.playback.current_song_num == 1
    playlist_id = backend.database.get_playlist_via_name('pair')
    assert backend.database.get_playlist_last_num(playlist_id) == 1

    # 重新打开同一 playlist → 恢复到上次位置
    response = _request(backend, 'open', song='pair')
    assert response['code'] == 0
    assert 'last played number detected' in response['msg']
    assert backend.playback.current_song_num == 1
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second


def test_open_song_already_in_playlist_switches_and_keeps_playlist(backend, audio_file, tmp_path):
    """Opening a song that is already in the current playlist switches to it.

    Guards two regressions of this branch: the IndexError from collapsing the
    in-memory playlist before switching to a song past the first one, and the
    playlist itself being collapsed to a single song.
    """
    first, second = _open_two_song_playlist(backend, audio_file, tmp_path)

    response = _request(backend, 'open', song=second)
    assert response['code'] == 0
    assert 'song in current playlist' in response['msg']
    assert backend.playback.current_song_num == 1
    assert len(backend.playback.current_song_info) == 2
    status = _request(backend, 'status')
    assert status['attachment']['path'] == second
    assert status['attachment']['playlist_len'] == 2


def test_open_song_already_in_playlist_refreshes_song_info(backend, audio_file, tmp_path):
    """The switched song's in-memory entry is re-read from the library."""
    first, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    song_id = backend.database.get_song_via_path(second)
    backend.database.set_song_meta(song_id, 'name', 'Renamed')

    response = _request(backend, 'open', song=second)
    assert response['code'] == 0
    assert 'Renamed' in response['msg']
    status = _request(backend, 'status')
    assert status['attachment']['name'] == 'Renamed'
    assert backend.playback.current_song_info[1]['name'] == 'Renamed'
    assert len(backend.playback.current_song_info) == 2


def test_open_playlist_first_time_starts_at_zero(backend, audio_file, tmp_path):
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    # 首次打开:last_num 不存在 → 走 else 分支,写 0 并从头播,无恢复消息
    assert backend.playback.current_song_num == 0
    playlist_id = backend.database.get_playlist_via_name('pair')
    assert backend.database.get_playlist_last_num(playlist_id) == 0


def test_switch_saves_playlist_last_num(backend, audio_file, tmp_path):
    first, second = _open_two_song_playlist(backend, audio_file, tmp_path)
    playlist_id = backend.database.get_playlist_via_name('pair')
    assert backend.database.get_playlist_last_num(playlist_id) == 0

    _request(backend, 'switch', number=2)
    assert backend.database.get_playlist_last_num(playlist_id) == 1

    _request(backend, 'switch', number=1)
    assert backend.database.get_playlist_last_num(playlist_id) == 0


def test_set_current_song_does_not_overwrite_last_num(backend, audio_file, tmp_path):
    # _set_current_song 初始化 current_song_num=0 时不应写库(update_database=False)
    first, _ = _open_two_song_playlist(backend, audio_file, tmp_path)
    playlist_id = backend.database.get_playlist_via_name('pair')

    _request(backend, 'switch', number=2)
    assert backend.database.get_playlist_last_num(playlist_id) == 1

    # 打开单曲(不在当前列表)→ _set_current_song 被调用,不应把 playlist 的 last_num 覆盖成 0
    other_file = audio_file.replace('test_audio', 'test_other')
    _request(backend, 'open', song=other_file)
    assert backend.database.get_playlist_last_num(playlist_id) == 1


