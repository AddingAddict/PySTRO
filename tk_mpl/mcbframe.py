from mcbdriver import MCBDriver
import numpy as np
from tkinter import *
from tkinter import ttk

from time import time

import matplotlib
matplotlib.use('GTK3Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

class MCBFrame(ttk.Frame):
    def __init__(self, master, mcb_driver, ndet):
        ttk.Frame.__init__(self, master)
        
        self.driver = mcb_driver
        self.hdet = self.driver.open_detector(ndet)
        self.name, self.id = self.driver.get_config_name(ndet)
        
        self.label = ttk.Label(self,\
            text='{0:04d} {1}'.format(self.id, self.name.decode()))
        self.label.grid(column=0, row=0, sticky=W)
        
        self.fig = Figure(figsize=(12,3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.ax.set_xlim((0,2048))
        self.ax.set_ylim(bottom=0)
        self.ax.axes.get_xaxis().set_visible(False)
        self.ax.axes.get_yaxis().set_visible(False)
        self.ax.set_position([0, 0, 1, 1])
        
        self.counts = self.driver.get_data(self.hdet)
        self.ax.set_ylim(top=1<<int(self.counts.max()).bit_length())
        self.chans = self.ax.bar(np.arange(2048), self.counts, width=1,\
            align='edge', color='blue')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(column=0, row=1, sticky=(N, E, S, W))
        
        def update_plot(frame):
            self.counts = self.driver.get_data(self.hdet)
            for chan, count in zip(self.chans, self.counts):
                chan.set_height(count)
            self.ax.set_ylim(top=1<<int(self.counts.max()).bit_length())
            return self.chans
        
        self.anim = FuncAnimation(self.fig, update_plot, interval=200,\
            repeat=True, blit=True)
        
    def start(self):
        self.driver.comm(self.hdet, 'START')
        
    def stop(self):
        self.driver.comm(self.hdet, 'STOP')
        
    def clear(self):
        self.driver.comm(self.hdet, 'CLEAR')