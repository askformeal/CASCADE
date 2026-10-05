import sys
import time
from threading import Thread
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

from PIL import Image, ImageTk

from .logger import logger
from src.constants.paths import ICON_PATH
from src.constants.gui import (
    UPDATE_INTERVAL,
    FAMILY_FALLBACK,
    FONT_SIZE,
    ICON_SIZE,
    BALLOON_BG,
    BALLOON_OFFSET_X,
    BALLOON_OFFSET_Y,
    BALLOON_WINDUP,
    BALLOON_WRAP
    )
from src.config import CONFIG
from src.frontend.client import send_request
from src.frontend.snapshot import Snapshot
from src.frontend.tkinter_tools.balloon import Balloon
from .empty import GUI_EMPTY as EMPTY
from .main_window import MainWinMixin
from .playback import PlaybackMixin
from .playlist import PlaylistMixin
from .lyric import LyricMixin
from .lifecycle import LifecycleMixin

class GUI(tk.Tk, MainWinMixin, PlaybackMixin, PlaylistMixin, LyricMixin, LifecycleMixin):
    def __init__(self):
        self.force_english_job = None
        self.no_hotkey_widgets = []

        self.snapshot = Snapshot(self.poll_request, empty=EMPTY)

        tk.Tk.__init__(self)
        MainWinMixin.__init__(self)
        PlaybackMixin.__init__(self)
        PlaylistMixin.__init__(self)
        LyricMixin.__init__(self)
        LifecycleMixin.__init__(self)

        self.balloon = Balloon(
            self,
            bg=BALLOON_BG,
            wrap_len=BALLOON_WRAP,
            offset_x=BALLOON_OFFSET_X,
            offset_y=BALLOON_OFFSET_Y,
            windup=BALLOON_WINDUP
            )

        self.withdraw()

        default_font = tkfont.nametofont("TkDefaultFont")
        available_families = tuple(map(lambda x: x.lower(), tkfont.families()))
        for i, family in enumerate((CONFIG.gui_font, *FAMILY_FALLBACK)):
            if family != '' and family.lower() in available_families:
                default_font.config(family=family)
                logger.debug(f'Fallback to the {i+1}th font: {family}')
                break
        else:
            logger.debug('No font in fallback chain available, use default')
        
        self.font_family = default_font.actual()['family']
        
        self.font = self.get_font(size=FONT_SIZE)

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

    def get_font(self, *args, family=None, **kwargs):
        if family is None:
            family = self.font_family
        return tkfont.Font(*args, family=family, **kwargs)

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
        self._update_main_window()

        if not self.window_ready:
            self.update_idletasks()
            x = (self.winfo_screenwidth() - self.winfo_reqwidth()) // 2
            y = (self.winfo_screenheight() - self.winfo_reqheight()) // 2
            self.geometry(f'+{x}+{y}')

            self.deiconify()
            self.window_ready = True
        self.balloon.refresh()

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
