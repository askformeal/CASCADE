import sys
import time
from threading import Thread
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
import webbrowser
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

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
        self.force_english_job = None

        self.old_playlists = []

        self.no_hotkey_widgets = []

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

        self.update_idletasks()
        if sys.platform == 'win32':
            self.imm = ctypes.windll.imm32
            self.user32 = ctypes.windll.user32
            self.user32.GetParent.restype = wintypes.HWND
            self.user32.GetParent.argtypes = [wintypes.HWND]
            self.imm.ImmGetContext.restype = ctypes.c_void_p
            self.imm.ImmGetContext.argtypes = [wintypes.HWND]
            self.imm.ImmReleaseContext.argtypes = [wintypes.HWND, ctypes.c_void_p]
            self.imm.ImmSetOpenStatus.argtypes = [ctypes.c_void_p, wintypes.BOOL]
            self.imm.ImmSetOpenStatus.restype = wintypes.BOOL

            self.bind('<FocusIn>', self._on_focus_in)
            self._on_focus_in()
        else:
            logger.debug('Non-windows platform detected. Auto switching to English input method will not be enabled')

        logger.debug(f'{__name__} initialized')

    def _on_focus_in(self, *_):
        if self.force_english_job is not None:
            self.after_cancel(self.force_english_job)
        self.force_english_job = self.after(100, self._force_english)

    def _force_english(self):
        hwnd = wintypes.HWND(self.user32.GetParent(self.winfo_id()))
        himc = self.imm.ImmGetContext(hwnd)
        if himc is not None:
            self.imm.ImmSetOpenStatus(himc, False)
            self.imm.ImmReleaseContext(hwnd, himc)

    def hotkey(self, widget, sequence, func):
        widget.bind(sequence, self._hotkey_func(func))

    def _hotkey_func(self, func):
        def on_hotkey(event):
            if event.widget in self.no_hotkey_widgets:
                return None
            else:
                return func(event)
        return on_hotkey

    def _build_window(self):
        self.hotkey(self, '<Control-q>', self._exit)
        self.hotkey(self, '<Control-w>', self._exit)
        self.hotkey(self, '<Control-o>', self._on_open)
        self.hotkey(self, '<Control-a>', self._open_all)
        
        self.hotkey(self, '<F5>', self._reload)
        self.hotkey(self, '<Control-,>', self._open_config)
        
        self.hotkey(self, '<v>', self._toggle_lyric_visible)
        self.bind('<F11>', self._toggle_fullscreen)
        self.bind('<Alt-Return>', self._toggle_fullscreen)

        self.hotkey(self, '<Shift-F1>', self._show_about)

        self.online_icon = self.get_icon(ONLINE_ICON_PATH, (32, 23))
        self.offline_icon = self.get_icon(OFFLINE_ICON_PATH, (32, 23))

        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(
            label='Open...', 
            command=self._on_open,
            accelerator='Ctrl+O',
            underline=0
            )
        file_menu.add_command(label='Open all', 
                              command=self._open_all,
                              underline=5
                              )
        self.open_playlist_menu = tk.Menu(file_menu, tearoff=False)
        file_menu.add_cascade(
            label='Open playlist', 
            menu=self.open_playlist_menu, 
            underline=5
            )
        file_menu.add_separator()
        file_menu.add_command(label='Start backend', command=self._start_backend)
        file_menu.add_command(label='Reboot backend', command=self._reboot_backend)
        file_menu.add_command(label='Ping backend', command=self._check_backend)
        file_menu.add_command(label='Exit backend', command=lambda: self.send_command('exit'))
        file_menu.add_separator()
        file_menu.add_command(
            label='Exit', 
            command=lambda *_: self._exit(), 
            accelerator='Ctrl+Q',
            underline=0
            )

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(
            label='Reload',
            accelerator='F5',
            command=self._reload
        )
        edit_menu.add_command(
            label='Configure...',
            accelerator='Ctrl+,',
            command=self._open_config
            )

        view_menu = tk.Menu(menubar, tearoff=False)
        self.lyric_visible = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(
            label='Lyric',
            variable=self.lyric_visible,
            accelerator='V',
            command=self._apply_lyric_visible
            )
        view_menu.add_command(label='Minimize', command=lambda: self.iconify())
        self.fullscreen = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(
            label='Fullscreen',
            variable=self.fullscreen,
            accelerator='F11',
            command=self._apply_fullscreen
            )

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label='GitHub repository...', command=lambda: webbrowser.open(REPO_LINK))
        help_menu.add_command(label='License', command=self._show_license)
        help_menu.add_separator()
        help_menu.add_command(
            label='About',
            accelerator='Shift+F1',
            command=self._show_about
            )

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

        playback_frame = tk.Frame(main_frame)
        self.build_playback(playback_frame)

        playlist_frame = tk.Frame(main_frame)
        self.build_playlist(playlist_frame)

        playback_frame.pack(
            side='left', 
            fill='y',
            expand=True,
            padx=(0, 10)
        )

        playlist_frame.pack(
            side='right',
            fill='y',
            expand=True
        )


        self.lyric_pack = lambda: lyric_frame.pack(
            before=playback_frame,
            side='left',
            fill='y',
            padx=(0, 10),
            expand=True
        )
        self.lyric_unpack = lyric_frame.pack_forget
        self.lyric_pack()

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
        def check():
            response = self._send_gui_request(action='test_alive')
            code = response['code']
            msg = f'Received response with code {code}'
            detail = response['msg']
            if code == 0:
                self.after(0, messagebox.showinfo, title='Backend online', message=msg, detail=detail)
            else:
                self.after(0, messagebox.showerror, title='Connection failed', message=msg, detail=detail)
        Thread(target=check).start()

    def _start_backend(self):
        def start():
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
        Thread(target=start).start()

    def _reboot_backend(self):
        def reboot():
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
        Thread(target=reboot).start()

    def _reload(self, *_):
        self.send_command(action='load_last')

    def _on_open(self, *_):
        OpenDialogue(self)

    def _open_all(self, *_):
        self.send_command('play-all')

    def _toggle_fullscreen(self, *_):
        self.fullscreen.set(not self.fullscreen.get())
        self._apply_fullscreen()

    def _apply_fullscreen(self):
        self.attributes('-fullscreen', self.fullscreen.get())

    def _toggle_lyric_visible(self, *_):
        self.lyric_visible.set(not self.lyric_visible.get())
        self._apply_lyric_visible()

    def _apply_lyric_visible(self):
        if self.lyric_visible.get():
            self.lyric_pack()
        else:
            self.lyric_unpack()

    def _open_config(self, *_):
        self.process.spawn('src.frontend.config_gui')

    def _show_license(self):
        with open(LICENSE_PATH, 'r', encoding=ENCODING) as f:
            license_text = f.read()
        messagebox.showinfo('License', 'MIT License', detail=license_text)

    def _show_about(self, *_):
        app_name = 'Command-Line Audio Stream Capture And Decoding Engine'
        detail = (
            f'Version: {__version__}\n'
            f'Author: Edward\n'
            f'GitHub repository: {REPO_LINK}\n'
            f'E-Mail: muzhi1014@outlook.com\n'
            f'License: MIT\n'
        )
        messagebox.showinfo('C.A.S.C.A.D.E', app_name, detail=detail)

    def _exit(self, *_):
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
