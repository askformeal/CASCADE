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
    ICON_SIZE,
    DEV_COLOR
    )
from src.frontend.client import send_request, test_heartbeat
from src.frontend.snapshot import Snapshot
from src.utils.time_ import format_time
from .empty import GUI_EMPTY as EMPTY
from .playback import PlaybackMixin
from .playlist import PlaylistMixin
from .lyric import LyricMixin
from .open_dialogue import OpenDialogue

class GUI(tk.Tk, PlaybackMixin, PlaylistMixin, LyricMixin):
    def __init__(self):
        self.running = True
        self.backend_online = True
        self.window_ready = False
        self.dev_label_shown = False

        self.old_playlists = []

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
        self.online_icon = self.get_icon(ONLINE_ICON_PATH, (32, 23))
        self.offline_icon = self.get_icon(OFFLINE_ICON_PATH, (32, 23))

        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label='Open...', command=self._on_open, underline=0)
        file_menu.add_command(label='Open all', 
                              command=lambda: self.send_command('play-all'),
                              underline=5
                              )
        self.open_playlist_menu = tk.Menu(file_menu, tearoff=False)
        file_menu.add_cascade(label='Open playlist', menu=self.open_playlist_menu, underline=5)
        file_menu.add_separator()
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

        bottom_bar = tk.Frame(self)
        bottom_bar.pack(side='bottom', fill='x', padx=10, pady=(0,10))
        
        self.online_button = tk.Button(bottom_bar, command=lambda: Thread(target=self._check_backend).start())
        self.online_button.pack(side='right')

        self.run_time_label = tk.Label(bottom_bar, font=tkfont.Font(size=FONT_SIZE, weight='bold'))
        self.run_time_label.pack(side='left', padx=(0, 20))

        self.dev_label = tk.Label(bottom_bar, 
                                  font=tkfont.Font(size=FONT_SIZE+3, weight='bold'), 
                                  fg=DEV_COLOR,
                                  text='DEV'
                                  )

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

        if self.snapshot.playlists is EMPTY:
            current_playlists = []
        else:
            current_playlists = self.snapshot.playlists
        if current_playlists != self.old_playlists:
            
            self.old_playlists = current_playlists
            self.open_playlist_menu.delete(0, tk.END)
            for name in current_playlists:
                open_func = lambda name=name: self.send_command('open', song=name, type='playlist')
                self.open_playlist_menu.add_command(label=name, 
                                                    command=open_func)

        if self.backend_online:
            self.online_button.config(image=self.online_icon)
        else:
            self.online_button.config(image=self.offline_icon)

        if self.snapshot.run_time is not EMPTY:
            self.run_time_label.config(text=format_time(self.snapshot.run_time, unit='sec'))
        else:
            self.run_time_label.config(text='--:--:--')

        if (self.snapshot.dev is not EMPTY 
            and self.snapshot.dev
            and not self.dev_label_shown
            ):
            self.dev_label.pack(side='left')
            self.dev_label_shown = True

        if not self.window_ready:
            self.update_idletasks()
            x = (self.winfo_screenwidth() - self.winfo_reqwidth()) // 2
            y = (self.winfo_screenheight() - self.winfo_reqheight()) // 2
            self.geometry(f'+{x}+{y}')

            self.deiconify()
            self.window_ready = True

    def _send_gui_request(self, action, **kwargs):
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
        response = self._send_gui_request(action=action, **kwargs)
        return response.get('attachment', None)

    def send_command(self, action, **kwargs):
        if self.backend_online:
            if not kwargs.get('silent', False):
                logger.info(f'Send command: {action}')
            response = self._send_gui_request(action=action, **kwargs)
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

    def _check_backend(self):
        response = self._send_gui_request(action='test_alive')
        code = response['code']
        msg = f'Received response with code {code}'
        detail = response['msg']
        if code == 0:
            self.after(0, messagebox.showinfo, title='Backend online', message=msg, detail=detail)
        else:
            self.after(0, messagebox.showerror, title='Connection failed', message=msg, detail=detail)

    def _on_open(self):
        OpenDialogue(self)        

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
