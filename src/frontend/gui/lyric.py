import tkinter as tk

from src.constants.gui import LYRIC_CURRENT_BG, LYRIC_CURRENT_FG
from src.sentinels import SENTINELS
from src.utils.lyric import get_lyric_line
from .empty import GUI_EMPTY as EMPTY

class LyricMixin:
    def __init__(self):
        self.old_lyric = []

    def build_lyric(self, lyric_frame):
        self.lyric_box = tk.Listbox(lyric_frame, 
                                    justify='center', 
                                    font=self.font,
                                    width=40,
                                    selectbackground=LYRIC_CURRENT_BG,
                                    selectforeground=LYRIC_CURRENT_FG,
                                    activestyle='none'
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
                    lyric.append(line[1].strip())

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
            self.lyric_box.delete(0, tk.END)
            for line in lyric:
                self.lyric_box.insert(tk.END, line)

        self.lyric_box.select_clear(0, tk.END)
        self.lyric_box.select_set(index)
        if self.snapshot.player_status == 'playing':
            bbox = self.lyric_box.bbox(self.lyric_box.index('@0,0'))
            if bbox is not None:
                item_height = bbox[3]
                visible_lines = self.lyric_box.winfo_height() // item_height
                self.lyric_box.yview(max(0, index - (visible_lines // 2)))
        