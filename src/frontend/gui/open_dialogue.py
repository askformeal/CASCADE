import tkinter as tk

from src.constants.paths import ICON_PATH
from src.constants.gui import CANCEL_COLOR, OPEN_COLOR

class OpenDialogue(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master=master)
        self.withdraw()

        self.title('Open')
        self.iconbitmap(ICON_PATH)
        self.bind('<Escape>', lambda *_: self.destroy())
        self.bind('<Return>', self._on_open)

        self.config(padx=10, pady=10)

        entry_frame = tk.Frame(self)
        entry_frame.pack(pady=(0, 20))

        self.entry = tk.Entry(entry_frame, font=self.master.font)
        self.entry.pack(side='left', padx=(0,10))

        self.type_ = tk.StringVar()
        self.type_.set('Auto')
        type_menu = tk.OptionMenu(
            entry_frame,
            self.type_,
            'Auto',
            'Song',
            'Playlist',
            'File',
        )
        type_menu.pack(side='left')

        button_frame = tk.Frame(self)
        button_frame.pack()

        cancel_button = tk.Button(button_frame,
                                  text='Cancel',
                                  font=self.master.font,
                                  bg=CANCEL_COLOR,
                                  command=lambda: self.destroy()
                                  )
        cancel_button.pack(side='left', padx=(0,10))

        open_button = tk.Button(button_frame,
                                text='Open',
                                font=self.master.font,
                                bg=OPEN_COLOR,
                                command=self._on_open
                                )
        open_button.pack(side='left')

        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - self.winfo_reqwidth()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f'+{x}+{y}')

        self.deiconify()

        self.wait_visibility()
        self.grab_set()
        self.entry.focus_set()

    def _on_open(self, *_):
        song = self.entry.get()
        if song != '':
            type_ = {'Auto': 'auto',
                    'Song': 'song',
                    'Playlist': 'playlist',
                    'File': 'file'
                    }[self.type_.get()]
            self.master.after(0, self.master.send_command, action='open', song=song, type=type_)
        self.destroy()
