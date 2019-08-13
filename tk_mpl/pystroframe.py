from mcbdriver import MCBDriver
from mcbframe import MCBFrame
import numpy as np
from tkinter import *
from tkinter import ttk

class PySTROFrame(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding="12 12 12 12")
        
        self.driver = MCBDriver()
        self.det_max = self.driver.get_config_max()

        btnframe = ttk.Frame(self)
        btnframe.grid(column=0, row=0, sticky=(E,W))

        startbtn = ttk.Button(btnframe, text='START', command=self.start)
        startbtn.grid(column=0, row=0, sticky=(E,W))
        stopbtn = ttk.Button(btnframe, text='STOP', command=self.stop)
        stopbtn.grid(column=1, row=0, sticky=(E,W))
        clearbtn = ttk.Button(btnframe, text='CLEAR', command=self.clear)
        clearbtn.grid(column=2, row=0, sticky=(E,W))
        
        self.mcbframes = [None]*self.det_max
        for n in range(0, self.det_max):
            self.mcbframes[n] = MCBFrame(self, self.driver, ndet=n+1)
            self.mcbframes[n].grid(column=0, row=n+1, sticky=(N, E, S, W))
            
        for child in self.winfo_children():\
            child.grid_configure(padx=5, pady=5)
            
    def start(self):
        for mcbframe in self.mcbframes:
            mcbframe.start()
            
    def stop(self):
        for mcbframe in self.mcbframes:
            mcbframe.stop()
            
    def clear(self):
        for mcbframe in self.mcbframes:
            mcbframe.clear()