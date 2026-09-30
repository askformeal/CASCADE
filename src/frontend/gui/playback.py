import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from io import BytesIO

from PIL import Image, ImageTk

from .logger import logger
from src.constants.paths import (
    GUI_NO_COVER_PATH,
    PREV_SONG_ICON_PATH,
    NEXT_SONG_ICON_PATH,
    PLAY_ICON_PATH,
    PAUSE_ICON_PATH,
    UNMUTE_ICON_PATH,
    MUTE_ICON_PATH,
    LOOP_ICON_PATH,
    SHUFFLE_ICON_PATH,
    DICE_ICON_PATH
)
from src.constants.gui import FONT_SIZE, COVER_SIZE
from src.utils.time_ import format_time
from src.sentinels import SENTINELS
from src.frontend.cover import Cover
from .empty import GUI_EMPTY as EMPTY

class PlaybackMixin:
    def __init__(self):
        image = Image.open(GUI_NO_COVER_PATH)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        self.no_cover = buffer.getvalue()
        self.old_cover_hash = None

        self.cover = Cover(
            self.poll_request,
            self.no_cover,
            logger
        )

        self.progress_dragging = False
        self.volume_dragging = False
        
        self.unmute_icon = self.get_icon(UNMUTE_ICON_PATH, 18)
        self.mute_icon = self.get_icon(MUTE_ICON_PATH, 18)

        self.prev_icon = self.get_icon(PREV_SONG_ICON_PATH)
        self.next_icon = self.get_icon(NEXT_SONG_ICON_PATH)
        self.play_icon = self.get_icon(PLAY_ICON_PATH)
        self.pause_icon = self.get_icon(PAUSE_ICON_PATH)

        self.loop_icon = self.get_icon(LOOP_ICON_PATH)
        self.shuffle_icon = self.get_icon(SHUFFLE_ICON_PATH)
        self.dice_icon = self.get_icon(DICE_ICON_PATH)
        
    def build_playback(self, playback_frame):

        self.name_label = tk.Label(playback_frame, font=tkfont.Font(size=FONT_SIZE+6, weight='bold'))
        self.name_label.pack(pady=(0,15))

        self.artist_label = tk.Label(playback_frame, font=tkfont.Font(size=FONT_SIZE+2, weight='bold'))
        self.artist_label.pack(pady=(0,25))

        self.cover_label = tk.Label(playback_frame)

        # self.cover_label.pack(fill='both', expand=True, pady=(0, 50))
        self.cover_label.pack(pady=(0, 50))

        scale_frame = tk.Frame(playback_frame)

        self.progress_scale = tk.Scale(
            scale_frame, 
            from_=0, 
            orient='horizontal', 
            sliderlength=20,
            showvalue=False,
            width=22
            )
        self.progress_scale.pack(side='left', padx=(0,30), fill='x', expand=True)
        self.progress_scale.bind('<ButtonPress-1>', lambda *_: setattr(self, 'progress_dragging', True))
        self.progress_scale.bind('<ButtonRelease-1>', self._set_time)

        self.mute_button = tk.Button(scale_frame, command=lambda: self.send_command('mute'))
        self.mute_button.pack(side='left', padx=(0,5))
        
        self.volume_scale = tk.Scale(scale_frame,
                                     from_=0,
                                     to=100,
                                     orient='horizontal',
                                    sliderlength=20,
                                     showvalue=False,
                                     length=100,
                                     width=22
                                     )
        self.volume_scale.pack(side='left')
        self.volume_scale.bind('<ButtonPress-1>', lambda *_: setattr(self, 'volume_dragging', True))
        self.volume_scale.bind('<ButtonRelease-1>', self._set_volume)

        
        bottom_bar = tk.Frame(playback_frame)
        self._build_bottom_bar(bottom_bar)
        
        bottom_bar.pack(side='bottom', fill='x', pady=(10, 0))
        ttk.Separator(playback_frame, orient='horizontal').pack(side='bottom', fill='x')
        scale_frame.pack(side='bottom', fill='x', pady=(0,20))
        

    def _build_bottom_bar(self, bottom_bar):
        
        prev_button = tk.Button(
            bottom_bar, 
            image=self.prev_icon, 
            command=lambda: self.send_command('prev')
            )
        prev_button.pack(side='left', padx=(0,5))
        
        self.play_button = tk.Button(
            bottom_bar, 
            command=lambda: self.send_command('toggle')
            )
        self.play_button.pack(side='left', padx=(0,5))
        
        next_button = tk.Button(
            bottom_bar, 
            image=self.next_icon, 
            command=lambda: self.send_command('next')
            )
        next_button.pack(side='left', padx=(0,30))

        self.loop_button = tk.Button(
            bottom_bar, 
            image=self.loop_icon,
            command=lambda: self.send_command('loop')
            )
        self.loop_button.pack(side='left', padx=(0,5))
        
        self.shuffle_button = tk.Button(
            bottom_bar, 
            image=self.shuffle_icon,
            command=lambda: self.send_command('shuffle')
            )
        self.shuffle_button.pack(side='left', padx=(0, 40))

        dice_button = tk.Button(
            bottom_bar,
            image=self.dice_icon,
            command=lambda: self.send_command('dice')
        )
        dice_button.pack(side='left')
        
        self.progress_label = tk.Label(
            bottom_bar, 
            font=tkfont.Font(size=FONT_SIZE+2, weight='bold'),
            relief='solid',
            bd=2,
            padx=5,
            pady=5
            )
        self.progress_label.pack(side='right', padx=(20, 0))
    
    def _set_time(self, *_):
        self.progress_dragging = False
        self.send_command('seek', time=str(self.progress_scale.get()), ms=True)

    def _set_volume(self, *_):
        self.volume_dragging = False
        self.send_command('volume', volume=str(self.volume_scale.get()))

    def update_playback(self):
        self.name_label.config(text=self.snapshot.display_name)
        self.artist_label.config(text=self.snapshot.artist)

        if self.snapshot.cover_hash is not EMPTY:
            cover = self.cover.get_cover(self.snapshot.cover_hash)
            cover_hash = self.snapshot.cover_hash
        else:
            cover = self.no_cover
            cover_hash = SENTINELS.NO_COVER

        if cover_hash != self.old_cover_hash:
            self.cover_image = Image.open(BytesIO(cover))
            self.cover_image = self.cover_image.resize(COVER_SIZE, Image.Resampling.LANCZOS)
            self.cover_image = ImageTk.PhotoImage(self.cover_image)
            self.cover_label.config(image=self.cover_image)
            self.old_cover_hash = cover_hash

        if (
            EMPTY not in (self.snapshot.time, self.snapshot.length) 
            and self.snapshot.time >= 0
            and self.snapshot.length >= 0
            ):
            if not self.progress_dragging:
                self.progress_scale.config(to=self.snapshot.length)
                self.progress_scale.set(self.snapshot.time)

            time_ = format_time(self.snapshot.time)
            length = format_time(self.snapshot.length)
            self.progress_label.config(text=f'{time_} / {length}')

        else:
            self.progress_scale.config(to=0)
            self.progress_scale.set(0)
            self.progress_label.config(text='--:--:-- / --:--:--')

        if self.snapshot.volume is not EMPTY and not self.volume_dragging:
            self.volume_scale.set(self.snapshot.volume)

        if self.snapshot.mute and self.snapshot.mute is not EMPTY:
            self.mute_button.config(image=self.mute_icon)
        else:
            self.mute_button.config(image=self.unmute_icon)

        if self.snapshot.player_status == 'playing':
            self.play_button.config(image=self.pause_icon)
        else:
            self.play_button.config(image=self.play_icon)

        if self.snapshot.loop and self.snapshot.loop is not EMPTY:
            self.loop_button.config(relief='sunken')
        else:
            self.loop_button.config(relief='raised')

        if self.snapshot.shuffle and self.snapshot.shuffle is not EMPTY:
            self.shuffle_button.config(relief='sunken')
        else:
            self.shuffle_button.config(relief='raised')
    