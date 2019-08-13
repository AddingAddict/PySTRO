from mcbdriver import MCBDriver
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np

class MCBWidget(QtWidgets.QWidget):
    def __init__(self, mcb_driver, ndet):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        # establish connection with MCB and get info from it
        self.driver = mcb_driver
        self.hdet = self.driver.open_detector(ndet)
        self.name, self.id = self.driver.get_config_name(ndet)
        self.counts = self.driver.get_data(self.hdet)
        
        # create label displaying MCB ID and name
        self.label = QtWidgets.QLabel('{0:04d} {1}'.format(self.id,\
            self.name.decode()))
            
        # create plot window
        self.plot = pg.PlotWidget()
        self.plot.setXRange(0, 2047, padding=0)
        self.plot.setYRange(0, 1<<int(self.counts.max()).bit_length(),\
            padding=0)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        
        # create initial histogram
        self.chans = 2048
        self.hist = pg.BarGraphItem(x=np.arange(self.chans),\
            height=self.counts, width=1, pen='b')
        self.plot.addItem(self.hist)
        
        # layout widgets
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.plot, 1, 0)
        
        # create QTimer to update plot
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(200)
        
    def update_plot(self):
        self.counts = self.driver.get_data(self.hdet)
        self.hist.setOpts(height=self.counts)
        self.plot.setYRange(0, 1<<int(self.counts.max()).bit_length(),\
            padding=0)
        
    def start(self):
        self.driver.comm(self.hdet, 'START')
        
    def stop(self):
        self.driver.comm(self.hdet, 'STOP')
        
    def clear(self):
        self.driver.comm(self.hdet, 'CLEAR')