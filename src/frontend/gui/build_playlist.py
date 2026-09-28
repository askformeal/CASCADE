import tkinter as tk

from src.constants.paths import SELECT_CURRENT_ICON_PATH, SWITCH_SELECTED_ICON_PATH

class PlaylistMixin:
    def build_playlist(self, playlist_frame):
        self.select_current_icon = self.get_icon(SELECT_CURRENT_ICON_PATH, 20)
        self.switch_selected_icon = self.get_icon(SWITCH_SELECTED_ICON_PATH, 20)

        top_bar = tk.Frame(playlist_frame)
        top_bar.pack(fill='x', padx=5, pady=(0, 10))

        select_current_button = tk.Button(
            top_bar, 
            image=self.select_current_icon, 
            command=self._select_current)
        select_current_button.pack(side='right', padx=(5, 0))

        switch_button = tk.Button(
            top_bar, 
            image=self.switch_selected_icon, 
            command=self._on_switch)
        switch_button.pack(side='right')


        box_frame = tk.Frame(playlist_frame)
        box_frame.pack(fill='both', expand=True)

        self.playlist_box = tk.Listbox(box_frame, font=self.font, width=25)
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

    def _on_switch(self, *_):
        selected = self.playlist_box.curselection()
        if len(selected) > 0:
            index = selected[0]
            index = self.song_numbers[index]
            self.send_command('switch', number=index + 1)
