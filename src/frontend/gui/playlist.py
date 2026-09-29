import tkinter as tk

from src.constants.paths import SELECT_CURRENT_ICON_PATH, SWITCH_SELECTED_ICON_PATH
from src.constants.gui import CURRENT_SONG_BG
from src.utils.misc import get_song_display_name
from .empty import GUI_EMPTY as EMPTY

class PlaylistMixin:
    def __init__(self):
        self.old_playlist = []
        self.old_current = None
        self.song_numbers = []
        self.playlist_empty = False
        
        self.select_current_icon = self.get_icon(SELECT_CURRENT_ICON_PATH, 20)
        self.switch_selected_icon = self.get_icon(SWITCH_SELECTED_ICON_PATH, 20)

    def build_playlist(self, playlist_frame):

        box_frame = tk.Frame(playlist_frame)
        box_frame.pack(fill='both', expand=True)

        self.playlist_box = tk.Listbox(box_frame, font=self.font, width=0)
        self.playlist_box.pack(side='left', fill='both', expand=True)

        scroll_bar_y = tk.Scrollbar(box_frame, orient='vertical')
        scroll_bar_x = tk.Scrollbar(playlist_frame, orient='horizontal')
        scroll_bar_y.pack(side='left', fill='y')
        scroll_bar_x.pack(fill='x')

        self.playlist_box.config(
            xscrollcommand=scroll_bar_x.set, 
            yscrollcommand=scroll_bar_y.set
            )

        scroll_bar_x.config(command=self.playlist_box.xview)
        scroll_bar_y.config(command=self.playlist_box.yview)

        self.playlist_box.bind('<Return>', self._on_switch)
        self.playlist_box.bind('<Double-Button-1>', self._on_switch)

        bottom_bar = tk.Frame(playlist_frame)
        bottom_bar.pack(side='bottom', fill='x', padx=5, pady=(10, 0))
        
        select_current_button = tk.Button(
            bottom_bar, 
            image=self.select_current_icon, 
            command=self._select_current)
        select_current_button.pack(side='right', padx=(5, 0))
        
        switch_button = tk.Button(
            bottom_bar, 
            image=self.switch_selected_icon, 
            command=self._on_switch)
        switch_button.pack(side='right')

    def _select_current(self):
        if self.snapshot.current_num is not EMPTY:
            index = self.song_numbers[self.snapshot.current_num]
            self.playlist_box.select_clear(0, tk.END)
            self.playlist_box.select_set(index)
            self.playlist_box.see(index)

    def _on_switch(self, *_):
        if not self.playlist_empty:
            selected = self.playlist_box.curselection()
            if len(selected) > 0:
                index = selected[0]
                index = self.song_numbers[index]
                self.send_command('switch', number=index + 1)

    def update_playlist(self):
        if (self.snapshot.current_songs is not EMPTY 
            and len(self.snapshot.current_songs) > 0
            ):
            self.playlist_empty = False
            playlist = []
            self.song_numbers = []
            for i, song in enumerate(self.snapshot.current_songs):
                name = get_song_display_name(song)
                playlist.append(f' {name} ')
                self.song_numbers.append(i)
        else:
            self.playlist_empty = True
            playlist = [' - No songs playing - ']
            self.song_numbers = []

        if playlist != self.old_playlist:
            self.old_playlist = playlist
            self.old_current = None

            self.playlist_box.delete(0, tk.END)
            for name in playlist:
                self.playlist_box.insert(tk.END, name)

        if self.snapshot.current_num is not EMPTY:
            if self.playlist_box.size() > 0:
                self.playlist_box.itemconfig(self.snapshot.current_num,
                                            bg=CURRENT_SONG_BG
                                            )

            if self.old_current is not None and self.old_current != self.snapshot.current_num:
                self.playlist_box.itemconfig(self.old_current,
                                            bg=self.playlist_box.cget('background')
                                            )
            self.old_current = self.snapshot.current_num

