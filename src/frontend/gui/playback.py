import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageTk

from .logger import logger
from src.constants.paths import (
    GUI_NO_COVER_PATH,
    SAVE_COVER_ICON_PATH,
    INFO_ICON_PATH,
    RELOAD_ICON_PATH,
    START_ICON_PATH,
    PREV_SONG_ICON_PATH,
    NEXT_SONG_ICON_PATH,
    PLAY_ICON_PATH,
    PAUSE_ICON_PATH,
    STOP_ICON_PATH,
    UNMUTE_ICON_PATH,
    MUTE_ICON_PATH,
    LOOP_ICON_PATH,
    SHUFFLE_ICON_PATH,
    REVERSE_ICON_PATH,
    DICE_ICON_PATH
)
from src.constants.gui import FONT_SIZE, INIT_COVER_SIZE
from src.constants.misc import IMAGE_FILE_TYPES
from src.config import CONFIG
from src.utils.time_ import format_time
from src.utils.image import test_save
from src.sentinels import SENTINELS
from src.frontend.cover import Cover
from .empty import GUI_EMPTY as EMPTY
from .info_popup import InfoPopUp

class PlaybackMixin:
    def __init__(self):
        image = Image.open(GUI_NO_COVER_PATH)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        self.no_cover = buffer.getvalue()
        self.old_cover_state = (None, None, None) # hash, width, height
        self.have_cover = False

        self.cover = Cover(
            self.poll_request,
            self.no_cover,
            logger
        )

        self.progress_dragging = False
        self.volume_dragging = False
        
        self.info_icon = self.get_icon(INFO_ICON_PATH)
        self.save_cover_icon = self.get_icon(SAVE_COVER_ICON_PATH)
        self.reload_icon = self.get_icon(RELOAD_ICON_PATH)
        self.start_icon = self.get_icon(START_ICON_PATH)

        self.unmute_icon = self.get_icon(UNMUTE_ICON_PATH, 18)
        self.mute_icon = self.get_icon(MUTE_ICON_PATH, 18)

        self.prev_icon = self.get_icon(PREV_SONG_ICON_PATH)
        self.next_icon = self.get_icon(NEXT_SONG_ICON_PATH)
        self.play_icon = self.get_icon(PLAY_ICON_PATH)
        self.pause_icon = self.get_icon(PAUSE_ICON_PATH)
        self.stop_icon = self.get_icon(STOP_ICON_PATH)

        self.loop_icon = self.get_icon(LOOP_ICON_PATH)
        self.shuffle_icon = self.get_icon(SHUFFLE_ICON_PATH)
        self.reverse_icon = self.get_icon(REVERSE_ICON_PATH)
        self.dice_icon = self.get_icon(DICE_ICON_PATH)
        
    def build_playback(self, playback_frame):
        self.hotkey(self, '<i>', self._open_info)
        self.hotkey(self, '<space>', self._toggle)
        self.hotkey(self, '<p>', self._prev)
        self.hotkey(self, '<n>', self._next)
        self.hotkey(self, '<x>', self._stop)
        self.hotkey(self, '<m>', self._mute)
        self.hotkey(self, '<s>', self._shuffle)
        self.hotkey(self, '<r>', self._loop)
        self.hotkey(self, '<b>', self._reverse)
        self.hotkey(self, '<d>', self._dice)
        
        playback_frame.bind('<Double-Button-1>', self._toggle)
        playback_frame.bind('<ButtonPress-1>', lambda *_: playback_frame.focus_set())
        self.hotkey(playback_frame, '<Left>', lambda *_: self._move_pos(False))
        self.hotkey(playback_frame, '<Right>', lambda *_: self._move_pos(True))
        self.hotkey(playback_frame, '<Shift-Left>', lambda *_: self._move_pos(False, long=True))
        self.hotkey(playback_frame, '<Shift-Right>', lambda *_: self._move_pos(True, long=True))

        self.hotkey(playback_frame, '<Up>', lambda *_: self._move_volume(True))
        self.hotkey(playback_frame, '<Down>', lambda *_: self._move_volume(False))

        top_bar = tk.Frame(playback_frame)
        top_bar.pack(fill='x')

        info_button = tk.Button(
            top_bar,
            image=self.info_icon,
            command=self._open_info
            )
        info_button.pack(side='right', padx=(7,0))
        self.balloon.bind_widget(info_button, 'Open song information (I)')

        save_cover_button = tk.Button(
            top_bar,
            image=self.save_cover_icon,
            command=self._save_cover
            )
        save_cover_button.pack(side='right', padx=(7,0))
        self.balloon.bind_widget(save_cover_button, 'Download cover')

        reload_button = tk.Button(
            top_bar,
            image=self.reload_icon,
            command=self._reload
        )
        reload_button.pack(side='right')
        self.balloon.bind_widget(reload_button, 'Reload (F5)')

        start_button = tk.Button(
            top_bar,
            image=self.start_icon,
            command=self._open_start,
        )
        start_button.pack(side='left')
        self.balloon.bind_widget(start_button, 'Start / Reboot (Ctrl+B)')

        self.name_label = tk.Label(playback_frame, font=self.get_font(size=FONT_SIZE+6, weight='bold'))
        self.name_label.pack(pady=(0,10))

        self.artist_label = tk.Label(playback_frame, font=self.get_font(size=FONT_SIZE+2, weight='bold'))
        self.artist_label.pack(pady=(0,15))

        self.cover_label = tk.Label(playback_frame, width=INIT_COVER_SIZE[0], height=INIT_COVER_SIZE[1])

        self.cover_label.bind('<Double-Button-1>', self._toggle)
        self.cover_label.bind('<ButtonPress-1>', lambda *_: self.cover_label.focus_set())

        scale_frame = tk.Frame(playback_frame)

        self.progress_scale = tk.Scale(
            scale_frame, 
            from_=0, 
            orient='horizontal', 
            sliderlength=20,
            showvalue=False,
            width=22,
            command=self._set_time
            )
        self.progress_scale.pack(side='left', padx=(0,30), fill='x', expand=True)
        self.progress_scale.bind('<ButtonPress-1>', lambda *_: setattr(self, 'progress_dragging', True))
        self.progress_scale.bind('<ButtonRelease-1>', lambda *_: setattr(self, 'progress_dragging', False))

        self.mute_button = tk.Button(scale_frame, command=self._mute)
        self.mute_button.pack(side='left', padx=(0,5))
        
        self.volume_scale = tk.Scale(scale_frame,
                                     from_=0,
                                     to=100,
                                     orient='horizontal',
                                    sliderlength=20,
                                     showvalue=False,
                                     length=100,
                                     width=22,
                                     command=self._set_volume
                                     )
        self.volume_scale.pack(side='left')
        self.volume_scale.bind('<ButtonPress-1>', lambda *_: setattr(self, 'volume_dragging', True))
        self.volume_scale.bind('<ButtonRelease-1>', lambda *_: setattr(self, 'volume_dragging', False))

        
        bottom_bar = tk.Frame(playback_frame)
        self._build_bottom_bar(bottom_bar)
        
        bottom_bar.pack(side='bottom', fill='x', pady=(10, 0))
        scale_frame.pack(side='bottom', fill='x')

        self.cover_label.pack(pady=(0,10), fill='both', expand=True)

    def _open_info(self, *_):
        InfoPopUp(self, self.snapshot.freeze())

    def _save_cover(self, *_):
        if self.have_cover:
            if self.snapshot.display_name is EMPTY:
                filename = 'cover.png'
            else:
                filename = f'{self.snapshot.display_name}.png'
            path = filedialog.asksaveasfilename(
                parent=self,
                title='Save cover',
                filetypes=(*IMAGE_FILE_TYPES, ('Any File', '*')),
                defaultextension='.png',
                initialfile=filename,
                )
            if path != '':
                logger.info(f'Save cover to {path}')
                image = Image.open(BytesIO(self.raw_cover))
                suffix = Path(path).suffix
                if not test_save(image, suffix=suffix):
                    logger.debug(f'Test save of {path} failed, convert to RGB')
                    image = image.convert('RGB')
                try:
                    image.save(path)
                except OSError as e:
                    messagebox.showerror('Failed to save cover', e)
        else:
            messagebox.showerror('Error', 'No cover available')

    def _build_bottom_bar(self, bottom_bar):
        
        prev_button = tk.Button(
            bottom_bar, 
            image=self.prev_icon, 
            command=self._prev
            )
        prev_button.pack(side='left', padx=(0,5))
        self.balloon.bind_widget(prev_button, 'Previous song (P)')
        
        self.play_button = tk.Button(
            bottom_bar, 
            command=self._toggle
            )
        self.play_button.pack(side='left', padx=(0,5))
        
        next_button = tk.Button(
            bottom_bar, 
            image=self.next_icon, 
            command=self._next
            )
        next_button.pack(side='left', padx=(0,20))
        self.balloon.bind_widget(next_button, 'Next song (N)')

        stop_button = tk.Button(
            bottom_bar,
            image=self.stop_icon,
            command=self._stop
        )
        stop_button.pack(side='left', padx=(0, 30))
        self.balloon.bind_widget(stop_button, 'Stop (X)')

        self.loop_button = tk.Button(
            bottom_bar, 
            image=self.loop_icon,
            command=self._loop
            )
        self.loop_button.pack(side='left', padx=(0,5))
        
        self.shuffle_button = tk.Button(
            bottom_bar, 
            image=self.shuffle_icon,
            command=self._shuffle
            )
        self.shuffle_button.pack(side='left', padx=(0, 5))
        
        self.reverse_button = tk.Button(
            bottom_bar, 
            image=self.reverse_icon,
            command=self._reverse
            )
        self.reverse_button.pack(side='left', padx=(0, 40))

        dice_button = tk.Button(
            bottom_bar,
            image=self.dice_icon,
            command=self._dice
        )
        dice_button.pack(side='left')
        self.balloon.bind_widget(dice_button, 'Randomly switch to a song (D)')
        
        self.progress_label = tk.Label(
            bottom_bar, 
            font=self.get_font(size=FONT_SIZE+2, weight='bold'),
            relief='solid',
            bd=2,
            padx=5,
            pady=5
            )
        self.progress_label.pack(side='right', padx=(20, 0))

    def _set_time(self, time_):
        if self.progress_dragging:
            self.send_command('seek', time=str(time_), ms=True, silent=True)

    def _set_volume(self, volume):
        if self.volume_dragging:
            self.send_command('volume', volume=str(volume), silent=True)

    def update_playback(self):
        self.name_label.config(text=self.snapshot.display_name)
        self.artist_label.config(text=self.snapshot.artist)

        if self.snapshot.cover_hash is not EMPTY:
            self.raw_cover = self.cover.get_cover(self.snapshot.cover_hash)
            cover_hash = self.snapshot.cover_hash
            self.have_cover = True
        else:
            self.raw_cover = self.no_cover
            cover_hash = SENTINELS.NO_COVER
            self.have_cover = False

        
        self.cover_label.update_idletasks()
        pad = 2 * (int(self.cover_label.cget("borderwidth")) + int(self.cover_label.cget("highlightthickness")))
        width = max(self.cover_label.winfo_width() - pad, 1)
        height = max(self.cover_label.winfo_height() - pad, 1)

        state = (cover_hash, width, height)
        if state != self.old_cover_state:
            self.cover_image = Image.open(BytesIO(self.raw_cover))
            image_width, image_height = self.cover_image.size
            ratio = min(
                height / image_height,
                width / image_width,
                )
            resize_width = round(image_width * ratio)
            resize_height = round(image_height * ratio)
            self.cover_image = self.cover_image.resize(
                (resize_width, resize_height), 
                Image.Resampling.LANCZOS
                )
            self.cover_image = ImageTk.PhotoImage(self.cover_image)
            self.cover_label.config(image=self.cover_image)
            self.old_cover_state = state

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
            self.balloon.bind_widget(self.mute_button, 'Unmute (M)')
        else:
            self.mute_button.config(image=self.unmute_icon)
            self.balloon.bind_widget(self.mute_button, 'Mute (M)')

        if self.snapshot.player_status == 'playing':
            self.play_button.config(image=self.pause_icon)
            self.balloon.bind_widget(self.play_button, 'Pause (Space)')
        else:
            self.play_button.config(image=self.play_icon)
            self.balloon.bind_widget(self.play_button, 'Resume (Space)')

        if self.snapshot.loop and self.snapshot.loop is not EMPTY:
            self.loop_button.config(relief='sunken')
            self.balloon.bind_widget(self.loop_button, 'Turn off loop (R)')
        else:
            self.loop_button.config(relief='raised')
            self.balloon.bind_widget(self.loop_button, 'Turn on loop (R)')

        if self.snapshot.shuffle and self.snapshot.shuffle is not EMPTY:
            self.shuffle_button.config(relief='sunken')
            self.balloon.bind_widget(self.shuffle_button, 'Turn off shuffle (S)')
        else:
            self.shuffle_button.config(relief='raised')
            self.balloon.bind_widget(self.shuffle_button, 'Turn on shuffle (S)')

        if self.snapshot.reverse and self.snapshot.reverse is not EMPTY:
            self.reverse_button.config(relief='sunken')
            self.balloon.bind_widget(self.reverse_button, 'Turn off reverse playback (B)')
        else:
            self.reverse_button.config(relief='raised')
            self.balloon.bind_widget(self.reverse_button, 'Turn on reverse playback (B)')

    def _toggle(self, *_):
        self.send_command('toggle')

    def _prev(self, *_):
        self.send_command('prev')

    def _next(self, *_):
        self.send_command('next')

    def _stop(self, *_):
        self.send_command('stop')        

    def _mute(self, *_):
        self.send_command('mute')
    
    def _loop(self, *_):
        self.send_command('loop')

    def _shuffle(self, *_):
        self.send_command('shuffle')
    
    def _reverse(self, *_):
        self.send_command('reverse')

    def _dice(self, *_):
        self.send_command('dice')

    def _move_volume(self, increase):
        if increase:
            prefix = '+'
        else:
            prefix = '-'
        step = f'{prefix}{CONFIG.gui_volume_step}'
        self.send_command('volume', volume=step, silent=True)

    def _move_pos(self, forward, long=False):
        if forward:
            prefix = '+'
        else:
            prefix = '-'
        if long:
            step = CONFIG.gui_pos_step_long
        else:
            step = CONFIG.gui_pos_step
        self.send_command('seek', time=f'{prefix}{step * 1000}', ms=True, silent=True)
        