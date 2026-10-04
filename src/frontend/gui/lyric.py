import tkinter as tk

from src.constants.paths import (
    ONLINE_LYRIC_ICON_PATH,
    LOCAL_LYRIC_ICON_PATH,
    RESET_OFFSET_ICON_PATH
)
from src.constants.gui import (
    LYRIC_BG,
    LYRIC_FG,
    LYRIC_CURRENT_BG, 
    LYRIC_CURRENT_FG, 
    SCROLL_EVENTS,
    MAX_OFFSET
    )
from src.config import CONFIG
from src.sentinels import SENTINELS
from src.utils.lyric import get_lyric_line
from .empty import GUI_EMPTY as EMPTY

class LyricMixin:
    def __init__(self):
        self.old_lyric = []
        self.old_index = None
        self.scroll_on = True
        self.bound_scroll = {}

        self.offset_dragging = False

        self.online_lyric_icon = self.get_icon(ONLINE_LYRIC_ICON_PATH)
        self.local_lyric_icon = self.get_icon(LOCAL_LYRIC_ICON_PATH)
        self.reset_offset_icon = self.get_icon(RESET_OFFSET_ICON_PATH)

    def build_lyric(self, lyric_frame):
        self.hotkey(self, '<backslash>', self._reset_offset)
        self.hotkey(self, '<[>', lambda *_: self._move_offset(False))
        self.hotkey(self, '<]>', lambda *_: self._move_offset(True))
        self.hotkey(self, '<z>', self._toggle_online_lyric)

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
        self.lyric_box.pack(fill='both', expand=True, pady=(0, 10))

        offset_bar = tk.Frame(lyric_frame)
        offset_bar.pack(fill='x', padx=5, pady=(0,10))
        
        self.base_offset_label = tk.Label(offset_bar, font=self.font)
        self.base_offset_label.pack(side='left', padx=(0,10))
        self.offset_overlay_label = tk.Label(offset_bar, font=self.font)
        self.offset_overlay_label.pack(side='left')
        self.total_offset = tk.Label(offset_bar, font=self.font)
        self.total_offset.pack(side='right')

        bottom_bar = tk.Frame(lyric_frame)
        bottom_bar.pack(side='bottom', fill='x', padx=10)

        self.online_lyric_button = tk.Button(bottom_bar, command=self._toggle_online_lyric)
        self.online_lyric_button.pack(side='right', padx=(10, 0))

        self.offset_scale = tk.Scale(bottom_bar, 
                                     font=self.font,
                                     from_=-MAX_OFFSET, 
                                     to=MAX_OFFSET,
                                     orient='horizontal',
                                     showvalue=False,
                                     command=self._set_offset
                                     )
        self.offset_scale.pack(side='right', fill='x', expand=True)
        self.offset_scale.bind('<ButtonPress-1>', lambda *_: setattr(self, 'offset_dragging', True))
        self.offset_scale.bind('<ButtonRelease-1>', lambda *_: setattr(self, 'offset_dragging', False))
        self.balloon.bind_widget(self.offset_scale, 'Offset overlay (ms)')
        
        offset_reset_button = tk.Button(bottom_bar,
                                        image=self.reset_offset_icon, 
                                        command=self._reset_offset
                                        )
        offset_reset_button.pack(side='left', padx=(0, 10))
        self.balloon.bind_widget(offset_reset_button, 'Reset offset (\\)')

    def _toggle_online_lyric(self, *_):
        self.send_command('lyric')

    def _reset_offset(self, *_):
        self.send_command('set_offset_overlay', offset=0)

    def _set_offset(self, *_):
        if self.offset_dragging:
            self.send_command(
                'set_offset_overlay',
                offset=self.offset_scale.get(),
                silent=True
                )

    def _move_offset(self, increase, *_):
        if increase:
            step = CONFIG.gui_offset_step
        else:
            step = -CONFIG.gui_offset_step
        current_offset = self.offset_scale.get()
        if current_offset + step > MAX_OFFSET:
            step = MAX_OFFSET - current_offset
        if current_offset + step < -MAX_OFFSET:
            step = -MAX_OFFSET - current_offset

        self.send_command('set_offset_overlay', offset=step, autoincrement=True)

    def update_lyric(self):
        self._update_lyric_box()

        if self.snapshot.online_lyric is not EMPTY and self.snapshot.online_lyric:
            self.online_lyric_button.config(image=self.online_lyric_icon)
            self.balloon.bind_widget(self.online_lyric_button, 'Switch to local source (Z)')
        else:
            self.online_lyric_button.config(image=self.local_lyric_icon)
            self.balloon.bind_widget(self.online_lyric_button, 'Switch to online source (Z)')

        if self.snapshot.offset_overlay is not EMPTY and not self.offset_dragging:
            self.offset_scale.set(self.snapshot.offset_overlay)

    def _update_lyric_box(self):
        if self.snapshot.lyric_offset is not EMPTY:
            self.base_offset_label.config(text=f'Base: {self.snapshot.lyric_offset}ms')
        if self.snapshot.offset_overlay is not EMPTY:
            self.offset_overlay_label.config(text=f'Overlay: {self.snapshot.offset_overlay}ms')
        if EMPTY not in (self.snapshot.lyric_offset, self.snapshot.offset_overlay):
            self.total_offset.config(text=f'Total: {self.snapshot.lyric_offset + self.snapshot.offset_overlay}ms')

        if self.snapshot.lyric_loading is not EMPTY and self.snapshot.lyric_loading:
            lyric = [' - Loading ... - ']
            index = 0
        else:
            index = 0
            if EMPTY not in (self.snapshot.time, 
                        self.snapshot.lyric,
                        self.snapshot.lyric_offset, 
                        self.snapshot.offset_overlay
                        ):
                lyric = []
                for line in self.snapshot.lyric:
                    lyric.append(f' {line[1].strip()} ')

                index = get_lyric_line(self.snapshot.lyric,
                                    self.snapshot.time,
                                    self.snapshot.lyric_offset + self.snapshot.offset_overlay
                                    )
                if index is SENTINELS.BEFORE_FIRST_LYRIC:
                    index = 0
                elif index is SENTINELS.EMPTY_LYRIC:
                    lyric = [' - Empty Lyric - ']
                    index = 0
            else:
                lyric = [' - No Lyric - ']

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
