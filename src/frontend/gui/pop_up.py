import tkinter as tk

from src.constants.paths import ICON_PATH
from src.frontend.tkinter_tools.to_center import to_center

class PopUp(tk.Toplevel):
    def __init__(self, master, *args, title='C.A.S.C.A.D.E', **kwargs):
        super().__init__(master, *args, **kwargs)
        self.withdraw()

        self.transient(self.master)
        self.title(title)
        self.iconbitmap(ICON_PATH)
        self.resizable(False, False)
        
        self.bind('<Escape>', lambda *_: self.destroy())
        self.bind('<Control-w>', lambda *_: self.destroy())

    def show_window(self):
        to_center(self, self.master)
        
        self.deiconify()
        
        self.wait_visibility()
        self.grab_set()
