from pystroframe import PySTROFrame
from tkinter import *
from tkinter import ttk

root = Tk()
root.title('PySTRO')

mainframe = PySTROFrame(root)
mainframe.grid(column=1, row=1, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(2, weight=1)

root.mainloop()