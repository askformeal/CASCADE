import tkinter as tk

from src.constants.gui import (
    LYRIC_BG,
    LYRIC_FG,
    LYRIC_CURRENT_BG, 
    LYRIC_CURRENT_FG, 
    SCROLL_EVENTS
    )
from src.sentinels import SENTINELS
from src.utils.lyric import get_lyric_line
from .empty import GUI_EMPTY as EMPTY

class LyricMixin:
    def __init__(self):
        self.old_lyric = []
        self.old_index = None
        self.scroll_on = True
        self.bound_scroll = {}

    def build_lyric(self, lyric_frame):
        self.lyric_box = tk.Listbox(lyric_frame, 
                                    bg=LYRIC_BG,
                                    fg=LYRIC_FG,
                                    selectbackground=LYRIC_BG, # invisible selection
                                    selectforeground=LYRIC_FG,
                                    justify='center', 
                                    font=self.font,
                                    width=0,
                                    activestyle='none',
                                    )
        self.lyric_box.pack(fill='both', expand=True)

    def update_lyric(self):
        if self.snapshot.lyric_loading is not EMPTY and self.snapshot.lyric_loading:
            lyric = ['Loading ...']
            index = 0
        else:
            lyric = []
            index = 0
            if EMPTY not in (self.snapshot.time, 
                        self.snapshot.lyric,
                        self.snapshot.lyric_offset, 
                        self.snapshot.offset_overlay
                        ):
                for line in self.snapshot.lyric:
                    lyric.append(f' {line[1].strip()} ')

                index = get_lyric_line(self.snapshot.lyric,
                                    self.snapshot.time,
                                    self.snapshot.lyric_offset + self.snapshot.offset_overlay
                                    )
                if index is SENTINELS.BEFORE_FIRST_LYRIC:
                    index = 0
                elif index is SENTINELS.EMPTY_LYRIC:
                    lyric = ['- No Lyric -']
                    index = 0

        if lyric != self.old_lyric:
            self.old_lyric = lyric
            self.old_index = None

            self.lyric_box.delete(0, tk.END)
            for line in lyric:
                self.lyric_box.insert(tk.END, line)
        
        if self.lyric_box.size() > 0:
            self.lyric_box.itemconfig(index, 
                                    bg=LYRIC_CURRENT_BG,
                                    fg=LYRIC_CURRENT_FG
                                    )
        
        if self.old_index is not None and self.old_index != index:
            self.lyric_box.itemconfig(self.old_index,
                                    bg=LYRIC_BG,
                                    fg=LYRIC_FG
                                    )
        self.old_index = index


        if self.snapshot.player_status == 'playing':
            self._disable_scroll()
            bbox = self.lyric_box.bbox(self.lyric_box.index('@0,0'))
            if bbox is not None:
                item_height = bbox[3]
                visible_lines = self.lyric_box.winfo_height() // item_height
                self.lyric_box.yview(max(0, index - (visible_lines // 2)))
        else:
            self._enable_scroll()

    def _disable_scroll(self):
        if self.scroll_on:
            self.scroll_on = False
            for event in SCROLL_EVENTS:
                self.bound_scroll[event] = self.lyric_box.bind(event, lambda *_: 'break', add='+')

    def _enable_scroll(self):
        if not self.scroll_on:
            self.scroll_on = True
            for event, func in self.bound_scroll.items():
                self.lyric_box.unbind(event, func)
            
            self.bound_scroll.clear()
