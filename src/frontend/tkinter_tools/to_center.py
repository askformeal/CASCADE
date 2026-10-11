import tkinter as tk

# move a window to the center of another
def to_center(top_level: tk.Toplevel, master: tk.Tk | tk.Toplevel):
    top_level.update_idletasks()
    x = master.winfo_x() + (master.winfo_width() - top_level.winfo_reqwidth()) // 2
    y = master.winfo_y() + (master.winfo_height() - top_level.winfo_reqheight()) // 2
    top_level.geometry(f'+{x}+{y}')
