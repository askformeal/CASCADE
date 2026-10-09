from src.sentinels import SENTINELS


def _playlist_song_ids(database, playlist_id):
    """get_playlist_songs returns song info dicts now; compare ids only."""
    songs = database.get_playlist_songs(playlist_id)
    ids = []
    for song in songs:
        ids.append(song['id'])
    return ids


def test_add_song_new(database):
    song_id, ignored = database.add_song(r'C:\music\song.flac')
    assert ignored is False
    assert database.song_exists(song_id)


def test_add_song_duplicate(database):
    first_id, ignored_first = database.add_song(r'C:\music\song.flac')
    second_id, ignored_second = database.add_song(r'C:\music\song.flac')
    assert ignored_first is False
    assert ignored_second is True
    assert first_id == second_id


def test_add_song_path_case_insensitive(database):
    _, ignored_first = database.add_song(r'C:\music\song.FLAC')
    _, ignored_second = database.add_song(r'c:\MUSIC\SONG.flac')
    assert ignored_first is False
    assert ignored_second is True


def test_get_song_via_path(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.get_song_via_path(r'C:\music\song.flac') == song_id
    assert database.get_song_via_path(r'C:\music\missing.flac') is SENTINELS.SONG_NOT_FOUND


def test_get_song_info(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    second_id, _ = database.add_song(r'C:\music\another.flac')
    info = database.get_song_info(song_id)
    assert info[0]['id'] == song_id
    assert info[0]['path'] == r'C:\music\song.flac'
    assert database.get_song_info(9999) == []
    batch = database.get_song_info([song_id, second_id])
    assert len(batch) == 2


def test_bind_alias(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.bind_alias(song_id, 'song') is SENTINELS.SUCCESS


def test_bind_alias_duplicate(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    database.bind_alias(song_id, 'song')
    assert database.bind_alias(song_id, 'song') is SENTINELS.ALIAS_EXISTS


def test_bind_alias_to_missing_song(database):
    assert database.bind_alias(9999, 'song') is SENTINELS.SONG_NOT_FOUND


def test_get_song_aliases(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.get_song_aliases(song_id) == []
    database.bind_alias(song_id, 'song')
    database.bind_alias(song_id, 'other')
    assert database.get_song_aliases(song_id) == ['song', 'other']
    assert database.get_song_aliases(9999) is SENTINELS.SONG_NOT_FOUND


def test_get_song_via_alias(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    database.bind_alias(song_id, 'song')
    assert database.get_song_via_alias('song') == song_id
    assert database.get_song_via_alias('missing') is SENTINELS.ALIAS_NOT_FOUND


def test_delete_alias(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    database.bind_alias(song_id, 'song')
    assert database.unbind_alias('song') is SENTINELS.SUCCESS
    assert database.unbind_alias('song') is SENTINELS.ALIAS_NOT_FOUND


def test_delete_song(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.delete_song(song_id) is SENTINELS.SUCCESS
    assert database.song_exists(song_id) is False
    assert database.delete_song(song_id) is SENTINELS.SONG_NOT_FOUND


def test_delete_song_cascades_aliases(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    database.bind_alias(song_id, 'song')
    assert database.get_song_via_alias('song') == song_id
    assert database.delete_song(song_id) is SENTINELS.SUCCESS
    assert database.get_song_via_alias('song') is SENTINELS.ALIAS_NOT_FOUND


def test_get_all_song_info_empty(database):
    assert database.get_all_song_info() == []


def test_get_all_song_info_after_add(database):
    database.add_song(r'C:\music\song.flac')
    database.add_song(r'C:\music\other.flac')
    info = database.get_all_song_info()
    assert len(info) == 2
    assert {row['path'] for row in info} == {r'C:\music\song.flac', r'C:\music\other.flac'}


def test_create_playlist(database):
    playlist_id, ignored = database.create_playlist('workout')
    assert ignored is False
    assert database.get_playlist_via_name('workout') == playlist_id


def test_create_playlist_duplicate(database):
    first_id, ignored_first = database.create_playlist('work')
    second_id, ignored_second = database.create_playlist('work')
    assert ignored_first is False
    assert ignored_second is True
    assert first_id == second_id


def test_add_song_to_playlist(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    playlist_id, _ = database.create_playlist('work')
    ignored = database.add_song_to_playlist(playlist_id, song_id)
    assert ignored is False
    assert _playlist_song_ids(database, playlist_id) == [song_id]


def test_add_song_to_playlist_duplicate(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    playlist_id, _ = database.create_playlist('work')
    assert database.add_song_to_playlist(playlist_id, song_id) is False
    assert database.add_song_to_playlist(playlist_id, song_id) is True
    assert _playlist_song_ids(database, playlist_id) == [song_id]


def test_get_playlist_via_name_missing(database):
    assert database.get_playlist_via_name('ghost') is SENTINELS.PLAYLIST_NOT_FOUND


def test_get_playlist_last_num_default_none(database):
    # 新建 playlist 从未播放过 → last_num 列是 NULL → 返回 None(不是 sentinel)
    playlist_id, _ = database.create_playlist('work')
    assert database.get_playlist_last_num(playlist_id) is None


def test_get_playlist_last_num_missing(database):
    assert database.get_playlist_last_num(9999) is SENTINELS.PLAYLIST_NOT_FOUND


def test_set_playlist_last_num(database):
    playlist_id, _ = database.create_playlist('work')
    database.set_playlist_last_num(playlist_id, 3)
    assert database.get_playlist_last_num(playlist_id) == 3


def test_set_playlist_last_num_missing(database):
    # playlist 不存在时静默失败,不抛异常
    database.set_playlist_last_num(9999, 3)


def test_del_song_from_playlist(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    playlist_id, _ = database.create_playlist('work')
    database.add_song_to_playlist(playlist_id, song_id)
    assert database.del_song_from_playlist(playlist_id, song_id) is SENTINELS.SUCCESS
    assert database.get_playlist_songs(playlist_id) == []


def test_del_song_from_playlist_song_not_in_playlist(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    other_song_id, _ = database.add_song(r'C:\music\other.flac')
    playlist_id, _ = database.create_playlist('work')
    database.add_song_to_playlist(playlist_id, song_id)
    assert database.del_song_from_playlist(playlist_id, other_song_id) is SENTINELS.PLAYLIST_SONG_NOT_FOUND


def test_del_song_from_playlist_song_not_found(database):
    playlist_id, _ = database.create_playlist('work')
    assert database.del_song_from_playlist(playlist_id, 9999) is SENTINELS.SONG_NOT_FOUND


def test_del_song_from_playlist_playlist_not_found(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.del_song_from_playlist(9999, song_id) is SENTINELS.PLAYLIST_NOT_FOUND


def test_del_playlist(database):
    playlist_id, _ = database.create_playlist('work')
    assert database.del_playlist(playlist_id) is SENTINELS.SUCCESS
    assert database.get_playlist_via_name('work') is SENTINELS.PLAYLIST_NOT_FOUND


def test_del_playlist_cascades_membership(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    playlist_id, _ = database.create_playlist('work')
    database.add_song_to_playlist(playlist_id, song_id)
    database.del_playlist(playlist_id)
    assert database.get_playlist_songs(playlist_id) is SENTINELS.PLAYLIST_NOT_FOUND
    assert database.song_exists(song_id)


def test_del_playlist_not_found(database):
    assert database.del_playlist(9999) is SENTINELS.PLAYLIST_NOT_FOUND


def _playlist_song_numbers(database, playlist_id):
    """Numbers ordered as the playlist is read, so 0..N-1 when nothing is wrong."""
    rows = database.execute('SELECT number FROM playlist_songs WHERE playlist_id = ? ORDER BY number, rowid', playlist_id).fetchall()
    numbers = []
    for row in rows:
        numbers.append(row['number'])
    return numbers


def _fill_playlist(database, playlist_id, names):
    """Add one song per name to the playlist and return their ids in that order."""
    song_ids = []
    for name in names:
        song_id, _ = database.add_song(fr'C:\music\{name}')
        database.add_song_to_playlist(playlist_id, song_id)
        song_ids.append(song_id)
    return song_ids


def test_add_song_to_playlist_numbers(database):
    # numbers start at 0 and increase by one for every appended song
    playlist_id, _ = database.create_playlist('work')
    song_ids = _fill_playlist(database, playlist_id, ['a.flac', 'b.flac', 'c.flac'])
    assert _playlist_song_numbers(database, playlist_id) == [0, 1, 2]


def test_add_song_to_playlist_after_removal_keeps_order(database):
    # removing the middle song leaves a gap, the next song is still appended last
    playlist_id, _ = database.create_playlist('work')
    song_ids = _fill_playlist(database, playlist_id, ['a.flac', 'b.flac', 'c.flac'])
    database.del_song_from_playlist(playlist_id, song_ids[1])
    new_song_id, _ = database.add_song(r'C:\music\d.flac')
    database.add_song_to_playlist(playlist_id, new_song_id)
    assert _playlist_song_ids(database, playlist_id) == [song_ids[0], song_ids[2], new_song_id]


def test_reorder_playlist(database):
    playlist_id, _ = database.create_playlist('work')
    song_ids = _fill_playlist(database, playlist_id, ['a.flac', 'b.flac', 'c.flac'])
    result = database.reorder_playlist(playlist_id, [song_ids[2], song_ids[0], song_ids[1]])
    assert result is SENTINELS.SUCCESS
    assert _playlist_song_ids(database, playlist_id) == [song_ids[2], song_ids[0], song_ids[1]]
    assert _playlist_song_numbers(database, playlist_id) == [0, 1, 2]


def test_reorder_playlist_twice_is_stable(database):
    playlist_id, _ = database.create_playlist('work')
    song_ids = _fill_playlist(database, playlist_id, ['a.flac', 'b.flac', 'c.flac'])
    order = [song_ids[1], song_ids[2], song_ids[0]]
    database.reorder_playlist(playlist_id, order)
    database.reorder_playlist(playlist_id, order)
    assert _playlist_song_ids(database, playlist_id) == order
    assert _playlist_song_numbers(database, playlist_id) == [0, 1, 2]


def test_reorder_playlist_not_found(database):
    assert database.reorder_playlist(9999, [1]) is SENTINELS.PLAYLIST_NOT_FOUND


def test_get_song_meta_none_by_default(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.get_song_meta(song_id, 'name') is None
    assert database.get_song_meta(song_id, 'artist') is None
    assert database.get_song_meta(song_id, 'album') is None


def test_set_song_meta(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.set_song_meta(song_id, 'name', 'Foo') is SENTINELS.SUCCESS
    assert database.set_song_meta(song_id, 'artist', 'Bar') is SENTINELS.SUCCESS
    assert database.set_song_meta(song_id, 'album', 'Baz') is SENTINELS.SUCCESS
    assert database.get_song_meta(song_id, 'name') == 'Foo'
    assert database.get_song_meta(song_id, 'artist') == 'Bar'
    assert database.get_song_meta(song_id, 'album') == 'Baz'


def test_set_song_meta_overwrite(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    database.set_song_meta(song_id, 'name', 'Foo')
    database.set_song_meta(song_id, 'name', 'New')
    assert database.get_song_meta(song_id, 'name') == 'New'


def test_set_song_meta_clear(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    database.set_song_meta(song_id, 'name', 'Foo')
    assert database.set_song_meta(song_id, 'name', SENTINELS.CLEAR_META) is SENTINELS.SUCCESS
    assert database.get_song_meta(song_id, 'name') is None


def test_get_song_meta_song_not_found(database):
    assert database.get_song_meta(9999, 'name') is SENTINELS.SONG_NOT_FOUND


def test_set_song_meta_song_not_found(database):
    assert database.set_song_meta(9999, 'name', 'Foo') is SENTINELS.SONG_NOT_FOUND


def test_get_song_meta_invalid_meta(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.get_song_meta(song_id, 'bogus') is SENTINELS.INVALID_META


def test_set_song_meta_invalid_meta(database):
    song_id, _ = database.add_song(r'C:\music\song.flac')
    assert database.set_song_meta(song_id, 'bogus', 'Foo') is SENTINELS.INVALID_META
