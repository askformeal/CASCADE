import time
from threading import Thread
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

from PIL import Image, ImageTk

from .logger import logger
from src.constants.paths import (
    ICON_PATH,
    ONLINE_ICON_PATH,
    OFFLINE_ICON_PATH
    )
from src.constants.frontend import HEARTBEAT_POLL_INTERVAL
from src.constants.gui import (
    UPDATE_INTERVAL,
    FONT_SIZE,
    ICON_SIZE
    )
from src.frontend.client import send_request, test_heartbeat
from src.frontend.snapshot import Snapshot
from src.utils.misc import get_song_display_name
from src.utils.time_ import format_time
from .empty import GUI_EMPTY as EMPTY
from .build_playback import PlaybackMixin
from .build_playlist import PlaylistMixin

class GUI(tk.Tk, PlaybackMixin, PlaylistMixin):
    def __init__(self):
        self.running = True
        self.backend_online = True
        self.window_ready = False

        self.snapshot = Snapshot(self.poll_request, empty=EMPTY)
        self.old_playlist = []
        self.song_numbers = []

        self.progress_dragging = False
        self.volume_dragging = False

        super().__init__()
        self.withdraw()
        
        self.font = tkfont.Font(
            size=FONT_SIZE
        )

        self.title('C.A.S.C.A.D.E')
        self.iconbitmap(ICON_PATH)
        self.protocol("WM_DELETE_WINDOW", self._exit)

        self._build_window()

        logger.debug(f'{__name__} initialized')

    def _build_window(self):
        self.online_icon = self.get_icon(ONLINE_ICON_PATH, 32)
        self.offline_icon = self.get_icon(OFFLINE_ICON_PATH, 32)

        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label='Exit', command=lambda *_: self._exit(), underline=0)

        menubar.add_cascade(label='File', menu=file_menu, underline=0)

        main_frame = tk.Frame(self)
        main_frame.pack(
            fill='both', 
            expand=True, 
            padx=10, 
            pady=(5, 10)
            )

        playback_frame = tk.Frame(main_frame)
        self.build_playback(playback_frame)
        playback_frame.pack(
            side='left', 
            fill='y', 
            expand=True,
            padx=(0, 10)
            )

        playlist_frame = tk.Frame(main_frame)
        self.build_playlist(playlist_frame)
        playlist_frame.pack(
            side='left',
            fill='y',
            expand=True
        )
        
        self.online_label = tk.Label(self)
        self.online_label.pack(anchor='e', padx=(0,5))

    def get_icon(self, path, size=None):
        if size is None:
            size = ICON_SIZE
        elif not isinstance(size, (list, tuple)):
            size = (size, size)
        image = Image.open(path)
        image = image.resize(size, Image.Resampling.LANCZOS)
        image = ImageTk.PhotoImage(image)
        return image

    def _update(self):
        while self.running:
            try:
                if self.backend_online:
                    self.snapshot.poll()
                else:
                    self.snapshot.reset()

                self.after(0, self._update_window)
            except Exception as e:
                logger.exception('An error occurred when updating')
            finally:
                time.sleep(UPDATE_INTERVAL)

    def _update_window(self):
        self._update_playback()
        self._update_playlist()

        if self.backend_online:
            self.online_label.config(image=self.online_icon)
        else:
            self.online_label.config(image=self.offline_icon)

        if not self.window_ready:
            x = (self.winfo_screenwidth() - self.winfo_reqwidth()) // 2
            y = (self.winfo_screenheight() - self.winfo_reqheight()) // 2
            self.geometry(f'+{x}+{y}')

            self.deiconify()
            self.window_ready = True

    def _update_playback(self):
        self.name_label.config(text=self.snapshot.display_name)
        self.artist_label.config(text=self.snapshot.artist)
        
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

    def _update_playlist(self):
        playlist = []
        self.song_numbers = []
        if self.snapshot.current_songs is not EMPTY:
            for i, song in enumerate(self.snapshot.current_songs):
                name = get_song_display_name(song)
                playlist.append(name)
                self.song_numbers.append(i)

        if playlist != self.old_playlist:
            self.old_playlist = playlist

            self.playlist_box.delete(0, tk.END)
            for name in playlist:
                self.playlist_box.insert(tk.END, name)

    def _select_current(self):
        if self.snapshot.current_num is not EMPTY:
            index = self.song_numbers[self.snapshot.current_num]
            self.playlist_box.select_clear(0, tk.END)
            self.playlist_box.select_set(index)
            self.playlist_box.see(index)

    def _sent_gui_request(self, action, **kwargs):
        silent = kwargs.get('silent', False)
        request = {
            'action':action, 
            'source':'gui',
            'notify_support':False,
            **kwargs
        }
        if not silent:
            logger.debug(f'Send request: {request}')

        response = send_request(**request)
        
        if not silent:
            logger.debug(f'Response received: {response}')

        return response

    def poll_request(self, action, **kwargs):
        response = self._sent_gui_request(action=action, **kwargs)
        return response.get('attachment', None)

    def send_command(self, action, **kwargs):
        if self.backend_online:
            logger.info(f'Send command: {action}')
            response = self._sent_gui_request(action=action, **kwargs)
            if response['code'] != 0:
                msg = response['msg']
                messagebox.showerror('Error', msg)

    def _monitor_heartbeat(self):
        while self.running:
            time.sleep(HEARTBEAT_POLL_INTERVAL)

            code = test_heartbeat()
            if code == 0:
                self.backend_online = True
            else:
                self.backend_online = False

    def _exit(self):
        logger.info('Exit GUI')
        self.running = False
        self.destroy()

    def run(self):
        Thread(target=self._monitor_heartbeat, daemon=True).start()
        Thread(target=self._update, daemon=True).start()
        logger.info('Start main loop')
        try:
            self.mainloop()
        except KeyboardInterrupt:
            ...

if __name__ == '__main__':
    GUI().run()
