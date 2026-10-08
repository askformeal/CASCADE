from threading import Thread
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from src import __version__
from src.constants.paths import (
    LICENSE,
    ONLINE_ICON,
    OFFLINE_ICON,
    START_ICON
    )
from src.constants.gui import DEV_COLOR, FONT_SIZE
from src.constants.misc import ENCODING, REPO_LINK
from src.utils.time_ import format_time
from .empty import GUI_EMPTY as EMPTY
from .menubar import MenubarMixin
from .open_dialogue import OpenDialogue
from .start_popup import StartPopUp

class MainWinMixin(MenubarMixin):
    def __init__(self):
        self.running = True
        self.dev_bar_on = tk.BooleanVar(value=False)
        self.backend_online = True
        self.window_ready = False
        self.dev_label_shown = False
        self.old_playlists = []

    def _build_window(self):
        self.hotkey(self, '<Control-q>', self._exit)
        self.hotkey(self, '<Control-w>', self._exit)
        self.hotkey(self, '<Control-o>', self._on_open)
        self.hotkey(self, '<Control-a>', self._open_all)
        self.hotkey(self, '<Control-b>', self._open_start)
    
        self.hotkey(self, '<F5>', self._reload)
        self.hotkey(self, '<Control-r>', self._reload)
        self.hotkey(self, '<Control-,>', self._open_config)
    
        self.hotkey(self, '<v>', self._toggle_lyric_visible)
        self.bind('<F11>', self._toggle_fullscreen)
        self.bind('<Alt-Return>', self._toggle_fullscreen)
        self.bind('<F12>', self._toggle_dev_bar)
    
        self.hotkey(self, '<Shift-F1>', self._show_about)
    
        self.online_icon = self.get_icon(ONLINE_ICON, (32, 23))
        self.offline_icon = self.get_icon(OFFLINE_ICON, (32, 23))
        self.start_icon = self.get_icon(START_ICON)
    
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        self.build_menubar(menubar)
    
        bottom_bar = tk.Frame(self)
        bottom_bar.pack(side='bottom', fill='x', padx=10, pady=(0,10))

        ttk.Separator(self).pack(side='bottom', fill='x', pady=(0,10), padx=3)
    
        self.online_button = tk.Button(bottom_bar, command=lambda: Thread(target=self.check_backend).start())
        self.online_button.pack(side='right', padx=(10,0))
        self.balloon.bind_widget(self.online_button, 'Ping backend')

        start_button = tk.Button(
            bottom_bar,
            image=self.start_icon,
            command=self._open_start,
        )
        start_button.pack(side='right')
        self.balloon.bind_widget(start_button, 'Start / Reboot (Ctrl+B)')
    
        self.dev_label = tk.Label(bottom_bar, 
                                  font=self.get_font(size=FONT_SIZE+3, weight='bold'), 
                                  fg=DEV_COLOR,
                                  text='DEV'
                                  )
        self.balloon.bind_widget(self.dev_label, 'Development mode on')
    
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
    
        left_separator = ttk.Separator(main_frame, orient='vertical')
        left_separator.pack(side='left', fill='y', padx=5)
        playback_frame.pack(
            side='left', 
            fill='y',
            expand=True,
            padx=(0, 10)
        )
        ttk.Separator(main_frame, orient='vertical').pack(side='left', fill='y', padx=5)
    
        playlist_frame.pack(
            side='right',
            fill='y',
            expand=True
        )
    
    
        self.lyric_pack = lambda: lyric_frame.pack(
            before=left_separator,
            side='left',
            fill='y',
            padx=(0, 10),
            expand=True
        )
        self.lyric_unpack = lyric_frame.pack_forget
        self.lyric_pack()

        self.dev_bar = tk.Frame(self)
        self.pack_dev_bar = lambda: self.dev_bar.pack(
            side='bottom',
            fill='x',
            before=bottom_bar,
            pady=(0,15),
            padx=5
            )

        dev_font = self.get_font(size=FONT_SIZE, weight='bold')

        self.run_time_label = tk.Label(self.dev_bar, font=dev_font)
        self.run_time_label.pack(side='left', padx=(0, 10))
        self.balloon.bind_widget(self.run_time_label, 'Backend run time')

        self.request_rate_label = tk.Label(self.dev_bar, font=dev_font)
        self.request_rate_label.pack(side='left')
        self.balloon.bind_widget(self.request_rate_label, 'Request received per second')


    def _update_main_window(self):
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
            run_time = format_time(self.snapshot.run_time, unit='sec')
        else:
            run_time = '--:--:--'
        self.run_time_label.config(text=f'Run time: {run_time}')
        
        if (self.snapshot.dev is not EMPTY 
            and self.snapshot.dev
            and not self.dev_label_shown
            ):
            self.dev_label.pack(side='left')
            self.dev_label_shown = True

        if self.snapshot.request_rate is not EMPTY:
            request_rate = f'{self.snapshot.request_rate:.2f}Hz'
        else:
            request_rate = EMPTY

        self.request_rate_label.config(text=f'Request rate: {request_rate}')

    def _toggle_dev_bar(self, *_):
        self.dev_bar_on.set(not self.dev_bar_on.get())
        self._apply_dev_bar()

    def _apply_dev_bar(self, *_):
        if self.dev_bar_on.get():
            self.pack_dev_bar()
        else:
            self.dev_bar.pack_forget()

    def _reload(self, *_):
        self.send_command(action='load_last')

    def _on_open(self, *_):
        OpenDialogue(self)

    def _open_all(self, *_):
        self.send_command('play-all')

    def _open_start(self, *_):
        StartPopUp(self)

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
        with open(LICENSE, 'r', encoding=ENCODING) as f:
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