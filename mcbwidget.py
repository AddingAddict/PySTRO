from mcbdriver import MCBDriver
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np

class MCBWidget(QtWidgets.QWidget):
    time_format = 'hh:mm:ss.zzz'
    
    def __init__(self, mcb_driver, ndet):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        # establish connection with MCB and get info from it
        self.driver = mcb_driver
        self.hdet = self.driver.open_detector(ndet)
        self.name, self.id = self.driver.get_config_name(ndet)
        
        self.counts = self.driver.get_data(self.hdet)
        
        self.real = self.get_real()
        self.realstr = '{0:.2f}'.format(self.real / 1000)
        self.live = self.get_live()
        self.livestr = '{0:.2f}'.format(self.live / 1000)
        self.dead = 0
        self.deadstr = '%'
        
        self.rpre = self.get_real_preset()
        self.rprestr = '{0:.2f}'.format(self.rpre / 1000)
        self.lpre = self.get_live_preset()
        self.lprestr = '{0:.2f}'.format(self.lpre / 1000)
        
        # create label displaying MCB ID and name
        self.label = QtWidgets.QLabel('{0:04d} {1}'.format(self.id,\
            self.name))
            
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
        
        # create a group for timing information
        self.timegrp = QtWidgets.QGroupBox('Time')
        self.timelayout = QtWidgets.QGridLayout()
        self.timegrp.setLayout(self.timelayout)
        
        # create timing labels
        self.reallbl = QtWidgets.QLabel(self.realstr)
        self.livelbl = QtWidgets.QLabel(self.livestr)
        self.deadlbl = QtWidgets.QLabel(self.deadstr)
        self.reallbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.livelbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.deadlbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.reallbl.setMinimumWidth(50)
        self.livelbl.setMinimumWidth(50)
        self.deadlbl.setMinimumWidth(50)
        
        # layout timing labels
        self.timelayout.addWidget(QtWidgets.QLabel('REAL: '), 0, 0)
        self.timelayout.addWidget(QtWidgets.QLabel('LIVE: '), 1, 0)
        self.timelayout.addWidget(QtWidgets.QLabel('DEAD: '), 2, 0)
        self.timelayout.addWidget(self.reallbl, 0, 1)
        self.timelayout.addWidget(self.livelbl, 1, 1)
        self.timelayout.addWidget(self.deadlbl, 2, 1)
        
        # create a group for preset limits
        self.presetgrp = QtWidgets.QGroupBox('Preset Limits')
        self.presetlayout = QtWidgets.QGridLayout()
        self.presetgrp.setLayout(self.presetlayout)
        
        # create preset labels
        self.rprelbl = QtWidgets.QLabel(self.rprestr)
        self.lprelbl = QtWidgets.QLabel(self.lprestr)
        self.rprelbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.lprelbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.rprelbl.setMinimumWidth(50)
        self.lprelbl.setMinimumWidth(50)
        
        # layout preset labels
        self.presetlayout.addWidget(QtWidgets.QLabel('REAL: '), 0, 0)
        self.presetlayout.addWidget(QtWidgets.QLabel('LIVE: '), 1, 0)
        self.presetlayout.addWidget(self.rprelbl, 0, 1)
        self.presetlayout.addWidget(self.lprelbl, 1, 1)
        
        # layout widgets
        self.layout.addWidget(self.label, 0, 0, 1, 2)
        self.layout.addWidget(self.plot, 1, 0, 2, 1)
        self.layout.addWidget(self.timegrp, 1, 1)
        self.layout.addWidget(self.presetgrp, 2, 1)
        
        # create QTimer to update plot
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(200)
        
    def update(self):
        # update plot
        self.counts = self.driver.get_data(self.hdet)
        
        self.plot.setYRange(0, 1<<int(self.counts.max()).bit_length(),\
            padding=0)
        self.hist.setOpts(height=self.counts)
            
        # update timing
        oldreal = self.real
        oldlive = self.live
        
        self.real = self.get_real()
        self.realstr = '{0:.2f}'.format(self.real / 1000)
        self.live = self.get_live()
        self.livestr = '{0:.2f}'.format(self.live / 1000)
        
        dreal = self.real - oldreal
        dlive = self.live - oldlive
        if dreal > dlive:
            self.dead = (1 - dlive/dreal) * 100
            self.deadstr = '{0:.2f} %'.format(self.dead)
        else:
            self.dead = 0
            self.deadstr = '%'
        
        self.reallbl.setText(self.realstr)
        self.livelbl.setText(self.livestr)
        self.deadlbl.setText(self.deadstr)
            
    def is_active(self):
        return self.driver.is_active(self.hdet)
        
    def start(self):
        self.driver.comm(self.hdet, 'START')
        
    def stop(self):
        self.driver.comm(self.hdet, 'STOP')
        
    def clear(self):
        self.driver.comm(self.hdet, 'CLEAR')
        
    def get_real(self):
        resp = self.driver.comm(self.hdet, 'SHOW_TRUE')
        msec = int(resp[2:-4]) * 20
        return msec
        
    def get_live(self):
        resp = self.driver.comm(self.hdet, 'SHOW_LIVE')
        msec = int(resp[2:-4]) * 20
        return msec
        
    def get_real_preset(self):
        resp = self.driver.comm(self.hdet, 'SHOW_TRUE_PRESET')
        msec = int(resp[2:-4]) * 20
        return msec
        
    def get_live_preset(self):
        resp = self.driver.comm(self.hdet, 'SHOW_LIVE_PRESET')
        msec = int(resp[2:-4]) * 20
        return msec