import tkinter as tk

from src.constants.paths.res.gui import (
    FILTER_ICON,
    SELECT_CURRENT_ICON, 
    SWITCH_SELECTED_ICON
    )
from src.constants.gui import (
    PLAYLIST_SELECT_BG,
    PLAYLIST_SELECT_FG,
    CURRENT_SONG_BG,
    PLAYLIST_MAX_CHAR,
    FONT_SIZE
    )
from src.utils.misc import get_song_display_name
from src.utils.text import strlen
from .empty import GUI_EMPTY as EMPTY

class PlaylistMixin:
    def __init__(self):
        self.old_playlist = []
        self.old_current = None
        self.song_indexes = []
        self.playlist_empty = False
        
        self.filter_icon = self.get_icon(FILTER_ICON, 20)
        self.select_current_icon = self.get_icon(SELECT_CURRENT_ICON, 20)
        self.switch_selected_icon = self.get_icon(SWITCH_SELECTED_ICON, 20)

    def build_playlist(self, playlist_frame):
        self.hotkey(self, '<c>', self._select_current)

        self.playlist_label = tk.Label(playlist_frame)
        self.playlist_label.pack()

        filter_frame = tk.Frame(playlist_frame)
        filter_frame.pack(fill='x', pady=(0,10))

        filter_label = tk.Label(filter_frame, image=self.filter_icon)
        filter_label.pack(side='left', padx=(0,3))
        self.balloon.bind_widget(filter_label, 'Filter songs')

        self.filter_entry = tk.Entry(
            filter_frame,
            width=20,
            font=self.font
            )
        self.filter_entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        self.no_hotkey_widgets.append(self.filter_entry)
        self.balloon.bind_widget(self.filter_entry, 'Filter songs')

        self.song_num_label = tk.Label(
            filter_frame,
            font=self.get_font(size=FONT_SIZE, weight='bold')
        )
        self.song_num_label.pack(side='left')

        box_frame = tk.Frame(playlist_frame)
        box_frame.pack(fill='both', expand=True)

        self.playlist_box = tk.Listbox(
            box_frame,
            font=self.font,
            width=0,
            selectbackground=PLAYLIST_SELECT_BG,
            selectforeground=PLAYLIST_SELECT_FG,
            selectborderwidth=4,
            activestyle='none',
            )
        self.playlist_box.pack(side='left', fill='both', expand=True)

        scroll_bar_y = tk.Scrollbar(box_frame, orient='vertical')
        scroll_bar_x = tk.Scrollbar(playlist_frame, orient='horizontal')
        scroll_bar_y.pack(side='left', fill='y')
        scroll_bar_x.pack(fill='x', pady=(0,10))

        self.playlist_box.config(
            xscrollcommand=scroll_bar_x.set, 
            yscrollcommand=scroll_bar_y.set
            )

        scroll_bar_x.config(command=self.playlist_box.xview)
        scroll_bar_y.config(command=self.playlist_box.yview)

        self.playlist_box.bind('<Return>', self._on_switch)
        self.playlist_box.bind('<Double-Button-1>', self._on_switch)
        self.playlist_box.bind('<FocusOut>', lambda *_: self.playlist_box.select_clear(0, tk.END))

        bottom_bar = tk.Frame(playlist_frame)
        bottom_bar.pack(side='bottom', fill='x', padx=5)
        
        select_current_button = tk.Button(
            bottom_bar, 
            image=self.select_current_icon, 
            command=self._select_current)
        select_current_button.pack(side='right', padx=(5, 0))
        self.balloon.bind_widget(select_current_button, 'Select playing song (C)')
        
        switch_button = tk.Button(
            bottom_bar, 
            image=self.switch_selected_icon, 
            command=self._on_switch)
        switch_button.pack(side='right')
        self.balloon.bind_widget(switch_button, 'Switch to selected song (Enter)')

    def _select_current(self, *_):
        if self.snapshot.current_num is not EMPTY:
            try:
                index = self.song_indexes.index(self.snapshot.current_num)
            except ValueError:
                ...
            else:
                self.playlist_box.select_clear(0, tk.END)
                self.playlist_box.select_set(index)
                self.playlist_box.activate(index)
                self.playlist_box.see(index)

    def _on_switch(self, *_):
        if not self.playlist_empty:
            selected = self.playlist_box.curselection()
            if len(selected) > 0:
                index = selected[0]
                index = self.song_indexes[index]
                self.send_command('switch', number=index + 1)

    def update_playlist(self):
        if self.snapshot.playing_all is not EMPTY and self.snapshot.playing_all:
            self.playlist_label.config(
                text='Library',
                font=self.get_font(
                    size=FONT_SIZE+2,
                    weight='bold',
                    slant='italic'
                    )
                )

        elif self.snapshot.playlist_name is not EMPTY:
            self.playlist_label.config(
                text=self.snapshot.playlist_name,
                font=self.get_font(size=FONT_SIZE+2, weight='bold')
                )
        else:
            self.playlist_label.config(
                text=''
                )

        filter_ = self.filter_entry.get()
        if (self.snapshot.current_songs is not EMPTY 
            and len(self.snapshot.current_songs) > 0
            ):
            total = len(self.snapshot.current_songs)
            
            playlist_signature = []
            self.playlist_empty = False
            playlist = []
            self.song_indexes = []
            
            keyword = filter_.strip().lower()
            for i, song in enumerate(self.snapshot.current_songs):
                name = get_song_display_name(song)
                artist = song.get('artist', None)
                if artist is None:
                    artist = ''
                if (
                    keyword in name.lower()
                    or keyword in artist.lower()
                    ):
                    song_str = name
                    if artist != '':
                        song_str += f' - {artist}'
                    playlist.append(f' {song_str} ')
                    self.song_indexes.append(i)
                    playlist_signature.append(song.copy())

            filtered = len(playlist)
        
        else:
            total = 0
            playlist_signature = []
            self.playlist_empty = True
            playlist = [' - No songs playing - ']
            self.song_indexes = []
            filtered = 0
                
        if playlist_signature != self.old_playlist:
            self.old_playlist = playlist_signature.copy()
            self.old_current = None


            self.playlist_box.delete(0, tk.END)
            for song_str in playlist:
                self.playlist_box.insert(tk.END, song_str)
            
            if len(playlist) > 0 and max(map(strlen, playlist)) > PLAYLIST_MAX_CHAR:
                self.playlist_box.config(width=PLAYLIST_MAX_CHAR)
            else:
                self.playlist_box.config(width=0) # 0 = auto width

        if self.snapshot.current_num is not EMPTY:
            try:
                current_index = self.song_indexes.index(self.snapshot.current_num)
            except ValueError:
                ...
            else:
                if current_index != self.old_current:
                    self._mark_item(current_index)
                    self.playlist_box.itemconfig(current_index,
                                                bg=CURRENT_SONG_BG
                                                )
                    if self.old_current is not None and self.old_current != current_index:
                        self._unmark_item(self.old_current)
                        self.playlist_box.itemconfig(self.old_current,
                                                    bg=self.playlist_box.cget('background')
                                                    )
                    self.old_current = current_index

        self.song_num_label.config(text=f'[{filtered}/{total}]')

    def _mark_item(self, index):
        text = self.playlist_box.get(index)
        self.playlist_box.delete(index)
        self.playlist_box.insert(index, f' [{text.strip()}] ')
    
    def _unmark_item(self, index):
        text = self.playlist_box.get(index)
        self.playlist_box.delete(index)
        self.playlist_box.insert(index, f' {text[2:-2]} ')

