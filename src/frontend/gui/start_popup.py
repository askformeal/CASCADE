import tkinter as tk

from .pop_up import PopUp

class StartPopUp(PopUp):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, title='Start / Reboot', **kwargs)
        self.config(padx=15, pady=10)

        check_frame = tk.Frame(self)
        check_frame.pack(pady=(0,20))


        self.continue_ = tk.BooleanVar(value=False)
        continue_check = tk.Checkbutton(
            check_frame,
            font=self.master.font,
            text='Continue',
            variable=self.continue_
            )
        continue_check.pack(side='left', padx=(0,10))
        
        self.dev = tk.BooleanVar(value=False)
        dev_check = tk.Checkbutton(
            check_frame,
            font=self.master.font,
            text='Development',
            variable=self.dev
            )
        dev_check.pack(side='left')

        button_frame = tk.Frame(self)
        button_frame.pack()

        start_button = tk.Button(
            button_frame,
            font=self.master.font,
            text='Start',
            command=self._on_start
            )
        start_button.pack(side='left', padx=(0,30))
        
        reboot_button = tk.Button(
            button_frame,
            font=self.master.font,
            text='Reboot',
            command=self._on_reboot
            )
        reboot_button.pack(side='left')

        self.show_window()

    def _on_start(self):
        self.master.start_backend(
            continue_=self.continue_.get(),
            dev=self.dev.get()
        )
        self.destroy()
    
    def _on_reboot(self):
        self.master.reboot_backend(
            continue_=self.continue_.get(), 
            dev=self.dev.get()
            )
        self.destroy()