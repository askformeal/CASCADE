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
from .empty import GUI_EMPTY as EMPTY
from .playback import PlaybackMixin
from .playlist import PlaylistMixin
from .lyric import LyricMixin

class GUI(tk.Tk, PlaybackMixin, PlaylistMixin, LyricMixin):
    def __init__(self):
        self.running = True
        self.backend_online = True
        self.window_ready = False

        self.snapshot = Snapshot(self.poll_request, empty=EMPTY)

        super().__init__()
        PlaybackMixin.__init__(self)
        PlaylistMixin.__init__(self)
        LyricMixin.__init__(self)

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

        lyric_frame = tk.Frame(main_frame)
        self.build_lyric(lyric_frame)
        lyric_frame.pack(
            side='left',
            fill='both',
            expand=True,
            padx=(0, 10)
        )

        playback_frame = tk.Frame(main_frame)
        self.build_playback(playback_frame)
        playback_frame.pack(
            side='left', 
            fill='both',
            expand=True,
            padx=(0, 10)
            )

        playlist_frame = tk.Frame(main_frame)
        self.build_playlist(playlist_frame)
        playlist_frame.pack(
            side='right',
            fill='both',
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
        self.update_playback()
        self.update_playlist()
        self.update_lyric()

        if self.backend_online:
            self.online_label.config(image=self.online_icon)
        else:
            self.online_label.config(image=self.offline_icon)

        if not self.window_ready:
            self.update_idletasks()
            x = (self.winfo_screenwidth() - self.winfo_reqwidth()) // 2
            y = (self.winfo_screenheight() - self.winfo_reqheight()) // 2
            self.geometry(f'+{x}+{y}')

            self.deiconify()
            self.window_ready = True

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
