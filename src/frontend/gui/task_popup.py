from datetime import datetime
from copy import deepcopy
import tkinter as tk
from tkinter import ttk
from src.frontend.tkinter_tools.scrolled_frame import ScrolledFrame

from src.constants.gui import (
    FONT_SIZE,
    TASK_REFRESH_INTERVAL,
    TASK_STATUS_FG,
    TASK_SCROLL_WIDTH,
    TASK_SCROLL_HEIGHT,
    TASK_RECORD_WRAP
    )
from .empty import GUI_EMPTY as EMPTY
from .pop_up import PopUp
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .core import GUI

class TaskPopUp(PopUp):
    def __init__(self, master: 'GUI', *args, **kwargs):
        super().__init__(master, *args, title='Tasks', **kwargs)
        self.master: 'GUI'
        self.old_tasks = None

        self.task_scroll = ScrolledFrame(self)
        self.task_scroll.canvas.config(
            width=TASK_SCROLL_WIDTH,
            height=TASK_SCROLL_HEIGHT
            )
        self.task_scroll.pack(fill='both', expand=True)

        self.after(0, self._refresh_tasks)
        self.show_window()

    def _refresh_tasks(self):
        tasks = deepcopy(self.master.snapshot.tasks)
        if tasks is not EMPTY and tasks != self.old_tasks:
            self.task_scroll.clear()
            
            ttk.Separator(self.task_scroll.frame).pack(fill='x', pady=(7,7))
            
            for task in tasks:
                task_frame = tk.Frame(self.task_scroll.frame)
                task_frame.pack(fill='x', expand=True, padx=5, pady=(0,3))

                status_fg = TASK_STATUS_FG[task['status']]
                tk.Label(
                    task_frame,
                    font=self.master.get_font(weight='bold', size=FONT_SIZE),
                    text=task['status'].capitalize(),
                    fg=status_fg
                    ).pack(side='right')
                
                tk.Label(
                    task_frame,
                    font=self.master.font,
                    text=task['name'],
                    anchor='w',
                    ).pack(side='left', padx=(0,10))

                log_frame = tk.Frame(self.task_scroll.frame)
                log_frame.pack(fill='x', expand=True, padx=5, pady=(0,7))

                if len(task['logs']) > 0:
                    time_ = datetime.fromtimestamp(round(task['logs'][-1][0]))
                    last_record = task['logs'][-1][1]
                    record_font = self.master.font
                else:
                    time_ = '---'
                    last_record = '[LOG EMPTY]'
                    record_font = self.master.get_font(size=FONT_SIZE, slant='italic', weight='bold')

                tk.Label(
                    log_frame,
                    font=self.master.font,
                    text='Last log:'
                    ).pack(side='left', padx=(0,5), anchor='n')

                record_frame = tk.Frame(log_frame)
                record_frame.pack(side='left', fill='x', expand=True, anchor='w')

                tk.Label(
                    record_frame,
                    font=record_font,
                    text=last_record,
                    wraplength=TASK_RECORD_WRAP,
                    justify='left'
                    ).pack(anchor='w')
                tk.Label(
                    record_frame,
                    font=record_font,
                    fg='#c28f03',
                    text=time_
                ).pack(anchor='w')

                       
                ttk.Separator(self.task_scroll.frame).pack(fill='x', pady=(0,7))
                
                
            self.old_tasks = deepcopy(tasks)

        self.after(TASK_REFRESH_INTERVAL, self._refresh_tasks)