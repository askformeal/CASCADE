import webbrowser
import tkinter as tk

from src.constants.misc import REPO_LINK

class MenubarMixin:
    def build_menubar(self, menubar):
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
            label='Exit GUI',
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