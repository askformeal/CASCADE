import tkinter as tk
from tkinter import ttk

from src.constants.paths import GUI_COPY_PATH
from src.constants.gui import FONT_SIZE
from src.utils.time_ import format_time
from .empty import GUI_EMPTY as EMPTY
from .pop_up import PopUp

class InfoPopUp(PopUp):
    def __init__(self, master, snapshot, *args, **kwargs):
        super().__init__(master, *args, title='Song information', **kwargs)
        
        self.config(padx=15, pady=5)

        self.copy_icon = self.master.get_icon(GUI_COPY_PATH)

        tk.Label(
            self,
            text='Song Information',
            font=self.master.get_font(size=FONT_SIZE+5, weight='bold')
            ).pack(pady=(0,10))

        basic_frame = self._build_section('Basic')
        self._build_field(basic_frame, 'File path', snapshot.path,
                          copy_button=True, copy_text=snapshot.path,
                          tooltip='Copy path')
        self._build_field(basic_frame, 'Library ID', snapshot.lib_id)
        self._build_field(basic_frame, 'Aliases', snapshot.aliases)
        self._build_field(basic_frame, 'Playlists', snapshot.added_playlists)
        
        meta_frame = self._build_section('Metadata')
        self._build_field(meta_frame, 'Name', snapshot.meta_name)
        self._build_field(meta_frame, 'Artist', snapshot.artist)
        self._build_field(meta_frame, 'Album', snapshot.album, is_end=True)

        tech_frame = self._build_section('Technical')
        duration = snapshot.duration
        if duration is EMPTY:
            duration = -1
        self._build_field(tech_frame, 'Duration', format_time(duration))
        bitrate = snapshot.bitrate
        if bitrate is not EMPTY:
            bitrate = f'{bitrate/1000:.10g} kbps'
        self._build_field(tech_frame, 'Bitrate', bitrate)
        self._build_field(tech_frame, 'Sample rate', snapshot.sample_rate)
        self._build_field(tech_frame, 'Channels', snapshot.channels, is_end=True)

        lyric_frame = self._build_section('Lyric', is_end=True)
        self._build_field(lyric_frame, 'Local file path', snapshot.lyric_path,
                          copy_button=True, copy_text=snapshot.lyric_path,
                          tooltip='Copy path')
        lyric_offset = snapshot.lyric_offset
        if lyric_offset is not EMPTY:
            lyric_offset = f'{lyric_offset}ms'
        self._build_field(lyric_frame, 'Offset', lyric_offset)

        close_button = tk.Button(
            self,
            font=self.master.font,
            text='Close',
            command=lambda: self.destroy()
            )
        close_button.pack(pady=(10,10))
        self.master.balloon.bind_widget(close_button, 'Close (Esc)')

        self.show_window()

    def _copy_text(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _build_section(self, name, is_end=False):
        if is_end:
            pady = 0
        else:
            pady = (0,10)

        frame = tk.LabelFrame(
            self, 
            text=name,
            font=self.master.get_font(size=FONT_SIZE+2, weight='bold'),
            padx=5,
            pady=3
            )
        frame.pack(pady=pady, fill='x')
        return frame
    
    def _build_field(self, master, name, values, copy_button=False, copy_text='', tooltip='', is_end=False):
        if not isinstance(values, (tuple, list)):
            values = (values,)
        if is_end:
            pady = 0
        else:
            pady = (0,3)
        frame = tk.Frame(master, bd=1)
        frame.pack(anchor='w', pady=pady, fill='x')
        
        tk.Label(
            frame,
            font=self.master.get_font(size=FONT_SIZE, weight='bold'),
            text=f'{name}:'
            ).pack(side='left', padx=(0,5))

        for i, value in enumerate(values):
            tk.Label(
                frame,
                font=self.master.font,
                text=str(value),
                wraplength=400,
                justify='left'
                ).pack(side='left')
            
            if i+1 < len(values):
                ttk.Separator(
                    frame, 
                    orient='vertical'
                    ).pack(
                        side='left',
                        fill='y',
                        padx=2,
                        pady=3
                        )

        if copy_button and copy_text is not EMPTY:
            button = tk.Button(
                frame,
                image=self.copy_icon,
                command=lambda text=copy_text: self._copy_text(text)
                )
            button.pack(side='left', padx=(10,0))
            self.master.balloon.bind_widget(button, tooltip)
        
        return frame
    