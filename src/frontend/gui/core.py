import time
from threading import Thread
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
import webbrowser

from PIL import Image, ImageTk

from .logger import logger
from src import __version__
from src.constants.misc import ENCODING, REPO_LINK
from src.constants.paths import (
    LICENSE_PATH,
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
from src.sentinels import SENTINELS
from src.frontend.client import send_request, test_heartbeat
from src.frontend.snapshot import Snapshot
from src.process import ProcessManager
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

        self.process = ProcessManager(logger)
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
        file_menu.add_command(label='Start backend', command=Thread(target=self._start_backend).start)
        file_menu.add_command(label='Reboot backend', command=Thread(target=self._reboot_backend).start)
        file_menu.add_command(label='Ping backend', command=Thread(target=self._check_backend).start)
        file_menu.add_command(label='Exit backend', command=lambda: self.send_command('exit'))
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=lambda *_: self._exit(), underline=0)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label='Configure...', command=lambda: self.process.spawn('src.frontend.config_gui'))

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label='Minimize', command=lambda: self.iconify())
        self.fullscreen = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label='Fullscreen', 
                                  variable=self.fullscreen,
                                  command=lambda: self.attributes('-fullscreen', self.fullscreen.get())
                                  )

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label='GitHub repository...', command=lambda: webbrowser.open(REPO_LINK))
        help_menu.add_command(label='License', command=self._show_license)
        help_menu.add_separator()
        help_menu.add_command(label='About', command=self._show_about)

        menubar.add_cascade(label='File', menu=file_menu, underline=0)
        menubar.add_cascade(label='Edit', menu=edit_menu, underline=0)
        menubar.add_cascade(label='View', menu=view_menu, underline=0)
        menubar.add_cascade(label='Help', menu=help_menu, underline=0)

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

    def _start_backend(self):
        result = self.process.start()
        if result is SENTINELS.SUCCESS:
            self.after(0, messagebox.showinfo, 
                       title='Backend started', 
                       message='Backend is now up and running'
                       )
        elif result is SENTINELS.BACKEND_ALREADY_RUNNING:
            self.after(0, messagebox.showinfo, 
                       title='Backend already running', 
                       message='Backend is already running'
                       )
        elif result is SENTINELS.FAILED_START_BACKEND:
            self.after(0, messagebox.showinfo, 
                       title='Error', 
                       message='Failed to start backend',
                       detail='Timed out waiting for backend to be alive'
                       )

    def _reboot_backend(self):
        result = self.process.reboot()
        if result is SENTINELS.SUCCESS:
            self.after(0, messagebox.showinfo, 
                       title='Backend rebooted', 
                       message='Backend is shutdown and restarted'
                       )
        elif result is SENTINELS.BACKEND_NOT_RUNNING:
            self.after(0, messagebox.showinfo, 
                       title='Error', 
                       message='Backend is not running',
                       )
        elif result is SENTINELS.FAILED_EXIT_BACKEND:
            self.after(0, messagebox.showinfo, 
                       title='Error', 
                       message='Failed to exit backend',
                       )
        elif result is SENTINELS.FAILED_START_BACKEND:
            self.after(0, messagebox.showinfo, 
                       title='Error', 
                       message='Failed to start backend',
                       detail='Backend is shutdown but failed to be restarted'
                       )            

    def _on_open(self):
        OpenDialogue(self)

    def _show_license(self):
        with open(LICENSE_PATH, 'r', encoding=ENCODING) as f:
            license_text = f.read()
        messagebox.showinfo('License', 'MIT License', detail=license_text)

    def _show_about(self):
        app_name = 'Command-Line Audio Stream Capture And Decoding Engine'
        detail = (
            f'Version: {__version__}\n'
            f'Author: Edward\n'
            f'GitHub repository: {REPO_LINK}\n'
            f'E-Mail: muzhi1014@outlook.com\n'
            f'License: MIT\n'
        )
        messagebox.showinfo('C.A.S.C.A.D.E', app_name, detail=detail)

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
