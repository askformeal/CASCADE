# CLI Commands

## Lifecycle

#### `cascade start` / `cascade reboot`

Start or restart backend.

`-c`/`--continue`: Resume last session.

`--dev`: Boot with an alternative development database.

#### `cascade exit`

Exit the backend

#### `cascade kill`

Terminate the backend process. May cause unpredictable consequences.

## Playback

#### `cascade status`

Show information about the current playback session.

```
╭──────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                  │
│  To Hell and Back - Sabaton [5 / 13]   <- [song name] - [artist] [number in current playlist]    │
│  [00:01:07 / 00:03:26] 33%     <- progress                                                       │
│                                                                                                  │
│  In library: Yes     <- if the song is added to the library                                      │
│  Album: Heroes                                                                                   │
│  Path: E:\Files\Musics\Sabaton\[2014] Sabaton - Heroes [16-44][qobuz]\05. To Hell and Back.flac  │
│                                                                                                  │
│  Lyric File Path: N/A     <- Local lyric file                                                    │
│  Player status: playing                                                                          │
│  Volume: 100%                                                                                    │
│  Mute: Off                                                                                       │
│                                                                                                  │
│  Shuffle: Off                                                                                    │
│  Loop: Off                                                                                       │
│  Reverse: Off                                                                                    │
│  Online Lyric: On                                                                                │
│                                                                                                  │
│  Audio Engine: Miniaudio                                                                         │
│                                                                                                  │
│  CASCADE backend has been running for 00:00:19                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `cascade open <song>`

Open a song / playlist.

#### `cascade play-all`

Open all songs in library.

#### `cascade reload`

Reopen the current song / playlist. Can make some changes take effect.

#### `cascade pause` / `cascade resume` / `cascade toggle`

Control play / pause.

#### `cascade stop`

Stop playback.

#### `cascade prev` / `cascade next`

Switch to the previous / next song.

#### `cascade list`

Show which songs are currently playing.

#### `cascade dice`

Jump to a random song in current playlist.

#### `cascade shuffle`

Toggle shuffle mode. Overrides reverse mode.

#### `cascade loop`

Toggle loop mode.

#### `cascade reverse`

Toggle reverse sequence mode. Overridden by shuffle mode.

#### `cascade lyric`

Switch lyric source: local / online

#### `cascade switch <num>`

Switch a specific song in the current playlist by its number.

#### `cascade seek <time>`

Jump to a specific time. Format: `HH:MM:SS`


#### `cascade jump <pct>`

Jump to progress by percentage.

#### `cascade replay`

Jump the beginning of the current song.

#### `cascade volume <pct>`

Set volume (percentage).

#### `cascade mute`

Toggle mute mode.

> `cascade seek` and `cascade volume` support setting the time / volume relatively by adding a +/- prefix to the value.
> For example, `cascade seek "-1:20"` jumps the progress backward by 1 minute 20 seconds.

> Note: if negative time is parsed as an option, wrap it in quotes like `cascade seek "-1:30"`

## Library

#### `cascade lib list`

Show all songs in library.

`-a` / `--show-aliases`: Show aliases of songs.

`-p` / `--show-playlists`: Show playlists each song is added to.

`-t` / `--show-tech`: Show technical information (bitrate, sample rate, etc).

#### `cascade lib info <songs>`

Show information of specific songs.

`-a` / `--show-aliases`: Show aliases of the songs.

`-p` / `--show-playlists`: Show playlists the songs are added to.

#### `cascade lib search <keyword>`

Search the library by keywords. Matches names, aliases, artists, albums and filenames.

`-o` / `--or`: Match keywords by OR instead of AND - only has to match one of the keywords instead of all of them.

#### `cascade lib add <paths>`

Add songs to library by their file paths.

Will automatically set metadata by value extracted from file, and bind the name as an alias. If the name metadata can't be extracted from the file, the filename will be used instead.

If a `.lrc` is found under same directory as one of the files, it will be automatically set as the song's local lyric file.

`-a` / `--aliases`: Bind aliases to the new songs. Must be same number as the paths.

`--skip-meta`: Do not set metadata automatically.

`--skip-alias`: Do not bind aliases automatically.

`--skip-lyric`: Do not set lyric files automatically.

`--loose-path`: Do not check the existence of files.

#### `cascade lib del <songs>`

Remove songs from library. Will not delete the file on disk.

#### `cascade lib scan <dir>`

Scan directory for audio files and add them to library. Will set metadata, aliases and lyric files automatically the same way as [`cascade lib add`](#cascade-lib-add-paths).

`-d` / `--dry-run`: Show result but do not add them to library.

`-r` / `--recurse`: Scan recursively.

`--playlist`: Also add all result to a playlist.

`--skip-meta`: Do not set metadata automatically.

`--skip-alias`: Do not bind aliases automatically.

`--skip-lyric`: Do not set lyric files automatically.

#### `cascade lib prune`

Scan the library for songs whose file no longer exists and remove them.

`-d` / `--dry-run`: Show result but do not remove them.

#### `cascade lib reset`

**Dangerous** Reset the whole database. **Irreversible**

`-y` / `--yes`: Skip confirmation.

### Metadata

#### `cascade lib meta set <song>`

Set the metadata of a song.

`--name <name>`: Set the name of the songs.

`--artist <artist>`: Set the artist of the song.

`--album <album>`: Set the album of the song.

#### `cascade lib meta read-file <song>`

Set the metadata of a song by value extract from its file.

`--name`: Set the name of the songs.

`--artist`: Set the artist of the song.

`--album`: Set the album of the song.

`--all`: Set all of above.

### Lyric

#### `cascade lib lyric show <song>`

Show set lyric file of a song.

#### `cascade lib lyric set <song> <path>`

Set the local lyric file of a song.

#### `cascade lib lyric fetch <songs>`

Download lyrics of songs from online sources.

> This command times out easily, and in that case, backend will continue to download and write files in background. I recommend you not to fetch for more than four songs at a time, as four is the maximum parallel downloading allowed.

> **For China Mainland users:** when fetching lyrics online, it is recommended to enable `netease_skip_proxy`. If you are there you'll know why.

#### `cascade lib lyric offset <song> <offset>`

Set the lyric offset of a song in milliseconds. 

Negative -> Earlier

Positive -> Later

Zero -> No offset

### Alias

#### `cascade lib alias list <song>`

Show all bound aliases of a song.

#### `cascade lib alias bind <song> <aliases>`

Bind aliases to a song.

#### `cascade lib alias unbind <aliases>`

Unbind aliases from their songs.

### Playlist

#### `cascade lib playlist list <playlist>`

List all songs in a playlist. If `<playlist>` argument is not provided, list all playlists in library.

`-a` / `--show-aliases`: Show aliases of songs.

`-p` / `--show-playlists`: Show playlists each song is added to.

`-t` / `--show-tech`: Show technical information (bitrate, sample rate, etc).

#### `cascade lib playlist create <name>`

Create a new playlist.

#### `cascade lib playlist add <playlist> <songs>`

Add songs to a playlist.

#### `cascade lib playlist kick <playlist> <songs>`

Remove songs from a playlist

#### `cascade lib playlist del <playlist>`

Delete a playlist from library. Will not delete the songs in it.

## Configure

`-d` / `--direct` / `--no-direct`: Access configuration directly without going through backend. Can only access options on the local machine. Available for all configure command.

#### `cascade config list`

Show all options. Example:
```
╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│  Name: lyric_x_offset                                                                                          │
│  Type: integer                                                                                                 │
│  Value: 0                                                                                                      │
│  Source: default value  <- not set in config file, use default value                                           │
│  Default Value: 0                                                                                              │
│                                                                                                                │
│  "Horizontal offset of lyric board from the middle of the screen (pixels, negative = left, positive = right)"  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `cascade config show <option>`

Show information of a specific option.

#### `cascade config set <option> <value>`

Set the value of an option.

`--overwrite-corrupt`: If the config file cannot be parsed as a valid TOML file, clear it and write the new option into it.

#### `cascade config unset <option>`

Remove an option from the config file. Will fallback to default value.

#### `cascade config open`

Open the config file. Will open on the machine the **backend** is running unless `--direct` is applied.

#### `cascade config path`

Show the path of the config file.

#### `cascade config gui`

Open configure GUI.

> For this command, `--direct` disable remote mode on startup and `--no-direct` will enable it. Both will override the `config_default_remote` option.

## Dashboard

#### `cascade dash`

Open dashboard.

## Reference a song

You can reference a song in library, e.g. to open it or show its information, by one of its aliases, its library ID, or its file path.

Pay attention that library ID is **NOT persisted**, as they are basically the row number of the song in the database. Make sure you check the ID right before using it.
