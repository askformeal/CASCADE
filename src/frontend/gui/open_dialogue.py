import tkinter as tk

from src.constants.gui import CANCEL_COLOR, OPEN_COLOR
from .pop_up import PopUp

class OpenDialogue(PopUp):
    def __init__(self, master):
        super().__init__(master, title='Open')
        
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

        self.show_window()
        self.entry.focus_set()

    def _on_open(self, *_):
        song = self.entry.get()
        if song != '':
            type_ = {'Auto': 'auto',
                    'Song': 'song',
                    'Playlist': 'playlist',
                    'File': 'file'
                    }[self.type_.get()]
            self.master.after(0, lambda: self.master.send_command(action='open', song=song, type=type_))
        self.destroy()
