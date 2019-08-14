from mcbdriver import MCBDriver
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from collections import deque

class MCBWidget(QtWidgets.QWidget):
    gate_index = {
        'OFF' : 0,
        'COIN': 1,
        'ANTI': 2
    }
    
    def __init__(self, mcb_driver, ndet):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        
        # create QValidator objects
        self.int_only = QtGui.QIntValidator()
        self.float_only = QtGui.QDoubleValidator()
        
        # establish connection with MCB and get info from it
        self.driver = mcb_driver
        self.hdet = self.driver.open_detector(ndet)
        self.name, self.id = self.driver.get_config_name(ndet)
        self.active = self.is_active()
        
        # create label displaying MCB ID and name
        self.label = QtWidgets.QLabel('{0:04d} {1}'.format(self.id,\
            self.name))
        
        # initialize sections of MCBWidget
        self.init_plotwidget()
        self.init_btngrp()
        self.init_timegrp()
        self.init_presetgrp()
        self.init_adcgrp()
        self.init_plotgrp()
        
        # layout widgets
        self.leftlayout = QtWidgets.QVBoxLayout()
        self.midlayout = QtWidgets.QVBoxLayout()
        self.rightlayout = QtWidgets.QVBoxLayout()
        
        self.layout.addLayout(self.leftlayout, 20)
        self.layout.addLayout(self.midlayout, 1)
        self.layout.addLayout(self.rightlayout, 1)
        
        self.leftlayout.addWidget(self.label)
        self.leftlayout.addWidget(self.plot)
        
        self.midlayout.addWidget(self.btngrp)
        self.midlayout.addWidget(self.timegrp)
        self.midlayout.addWidget(self.presetgrp)
        self.midlayout.addWidget(QtWidgets.QWidget(), 10)
        
        self.rightlayout.addWidget(self.adcgrp)
        self.rightlayout.addWidget(self.plotgrp)
        self.rightlayout.addWidget(QtWidgets.QWidget(), 10)
        
        # create QTimer to update plot
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(250)
        
    def init_plotwidget(self):
        self.counts = self.driver.get_data(self.hdet)
        
        # create plot window
        self.plot = pg.PlotWidget()
        self.plot.setXRange(0, 2047, padding=0)
        self.plot.setYRange(0, 1<<int(self.counts.max()).bit_length(),\
            padding=0)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.setMinimumWidth(1024)
        
        # create initial histogram
        self.chans = 2048
        self.hist = pg.BarGraphItem(x=np.arange(self.chans),\
            height=self.counts, width=1, pen='b')
        self.plot.addItem(self.hist)
        
    def init_btngrp(self):
        # create a group for control buttons
        self.btngrp = QtWidgets.QGroupBox('Data Acquisition')
        self.btnlayout = QtWidgets.QHBoxLayout()
        self.btngrp.setLayout(self.btnlayout)
        
        # create control buttons
        self.startbtn = QtWidgets.QPushButton('')
        self.stopbtn = QtWidgets.QPushButton('')
        self.clearbtn = QtWidgets.QPushButton('')
        
        # add icons to control buttons
        self.startbtn.setIcon(QtGui.QIcon('icons/start.png'))
        self.stopbtn.setIcon(QtGui.QIcon('icons/stop.png'))
        self.clearbtn.setIcon(QtGui.QIcon('icons/clear.png'))
        
        # add response functions for buttons
        self.startbtn.clicked.connect(self.start)
        self.stopbtn.clicked.connect(self.stop)
        self.clearbtn.clicked.connect(self.clear)
        
        # layout control buttons
        self.btnlayout.addWidget(self.startbtn)
        self.btnlayout.addWidget(self.stopbtn)
        self.btnlayout.addWidget(self.clearbtn)
        
        # enable/disable buttons
        if self.active:
            self.startbtn.setEnabled(False)
            self.stopbtn.setEnabled(True)
        else:
            self.startbtn.setEnabled(True)
            self.stopbtn.setEnabled(False)
        
    def init_timegrp(self):
        self.real = self.get_real()
        self.realstr = '{0:.2f}'.format(self.real / 1000)
        self.live = self.get_live()
        self.livestr = '{0:.2f}'.format(self.live / 1000)
        self.dead = 0
        self.deadstr = '%'
        self.dreals = deque([0]*4)
        self.dlives = deque([0]*4)
        
        # create a group for timing information
        self.timegrp = QtWidgets.QGroupBox('Timing')
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
        self.timelayout.addWidget(QtWidgets.QLabel('Real: '), 0, 0)
        self.timelayout.addWidget(QtWidgets.QLabel('Live: '), 1, 0)
        self.timelayout.addWidget(QtWidgets.QLabel('Dead: '), 2, 0)
        self.timelayout.addWidget(self.reallbl, 0, 1)
        self.timelayout.addWidget(self.livelbl, 1, 1)
        self.timelayout.addWidget(self.deadlbl, 2, 1)
        
    def init_presetgrp(self):
        self.rpre = self.get_real_preset()
        if self.rpre > 0:
            self.rprestr = '{0:.2f}'.format(self.rpre / 1000)
        else:
            self.rprestr = ''
        self.lpre = self.get_live_preset()
        if self.lpre > 0:
            self.lprestr = '{0:.2f}'.format(self.lpre / 1000)
        else:
            self.lprestr = ''
            
        # create a group for preset limits
        self.presetgrp = QtWidgets.QGroupBox('Preset Limits')
        self.presetlayout = QtWidgets.QGridLayout()
        self.presetgrp.setLayout(self.presetlayout)
        
        # create preset textboxes
        self.rpretxt = QtWidgets.QLineEdit(self.rprestr)
        self.lpretxt = QtWidgets.QLineEdit(self.lprestr)
        self.rpretxt.setValidator(self.float_only)
        self.lpretxt.setValidator(self.float_only)
        self.rpretxt.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.lpretxt.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.rpretxt.setMinimumWidth(50)
        self.lpretxt.setMinimumWidth(50)
        
        # layout preset widgets
        self.presetlayout.addWidget(QtWidgets.QLabel('Real: '), 0, 0)
        self.presetlayout.addWidget(QtWidgets.QLabel('Live: '), 1, 0)
        self.presetlayout.addWidget(self.rpretxt, 0, 1)
        self.presetlayout.addWidget(self.lpretxt, 1, 1)
        
        # enable/disable presets
        if self.active:
            self.rpretxt.setReadOnly(True)
            self.lpretxt.setReadOnly(True)
        else:
            self.rpretxt.setReadOnly(False)
            self.lpretxt.setReadOnly(False)
        
    def init_adcgrp(self):
        self.gate = self.get_gate()
        self.lld = self.get_lld()
        self.uld = self.get_uld()
        self.lldstr = str(self.lld)
        self.uldstr = str(self.uld)
        
        # create a group for ADC settings
        self.adcgrp = QtWidgets.QGroupBox('ADC Settings')
        self.adclayout = QtWidgets.QGridLayout()
        self.adcgrp.setLayout(self.adclayout)
        
        # create gate dropdown menu
        self.gatebox = QtWidgets.QComboBox()
        for option in ['Off', 'Coincidence', 'Anticoincidence']:
            self.gatebox.addItem(option)
        self.gatebox.setCurrentIndex(self.gate)
        
        # create discriminator textboxes
        self.lldtxt = QtWidgets.QLineEdit(self.lldstr)
        self.uldtxt = QtWidgets.QLineEdit(self.uldstr)
        self.lldtxt.setValidator(self.int_only)
        self.uldtxt.setValidator(self.int_only)
        self.lldtxt.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.uldtxt.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.lldtxt.setMinimumWidth(30)
        self.uldtxt.setMinimumWidth(30)
        
        # layout ADC widgets
        self.adclayout.addWidget(QtWidgets.QLabel('Gate: '), 0, 0, 1, 2)
        self.adclayout.addWidget(QtWidgets.QLabel('Lower Disc: '), 2, 0)
        self.adclayout.addWidget(QtWidgets.QLabel('Upper Disc: '), 3, 0)
        self.adclayout.addWidget(self.gatebox, 1, 0, 1, 2)
        self.adclayout.addWidget(self.lldtxt, 2, 1)
        self.adclayout.addWidget(self.uldtxt, 3, 1)
        
    def init_plotgrp(self):
        self.mode = 'Auto'
        
        # create a group for plot settings
        self.plotgrp = QtWidgets.QGroupBox('Plot Settings')
        self.plotlayout = QtWidgets.QGridLayout()
        self.plotgrp.setLayout(self.plotlayout)
        
        # create plot mode buttons
        self.logbtn = QtWidgets.QPushButton('Log')
        self.autobtn = QtWidgets.QPushButton('Auto')
        self.logbtn.setMinimumWidth(5)
        self.autobtn.setMinimumWidth(5)
        self.autobtn.setEnabled(False)
        
        # add response functions for buttons
        def log_click():
            self.mode = 'Log'
            self.logbtn.setEnabled(False)
            self.autobtn.setEnabled(True)
            
            self.plot.setYRange(0, 31, padding=0)
            logsafe = np.maximum(1, self.counts)
            self.hist.setOpts(height=np.log2(logsafe))
        def auto_click():
            self.mode = 'Auto'
            self.logbtn.setEnabled(True)
            self.autobtn.setEnabled(False)
            
            self.plot.setYRange(0, 1<<int(self.counts.max()).bit_length(),\
                padding=0)
            self.hist.setOpts(height=self.counts)
        self.logbtn.clicked.connect(log_click)
        self.autobtn.clicked.connect(auto_click)
        
        # layout plot widgets
        self.plotlayout.addWidget(QtWidgets.QLabel('Plot Mode: '), 0, 0, 1, 2)
        self.plotlayout.addWidget(QtWidgets.QLabel('# Channels: '), 2, 0, 1, 2)
        self.plotlayout.addWidget(self.logbtn, 1, 0)
        self.plotlayout.addWidget(self.autobtn, 1, 1)
        
    def update(self):
        # update plot
        self.counts = self.driver.get_data(self.hdet)
        
        if self.mode == 'Log':
            self.plot.setYRange(0, 31, padding=0)
            logsafe = np.maximum(1, self.counts)
            self.hist.setOpts(height=np.log2(logsafe))
        else:
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
        
        self.dreals.append(self.real - oldreal)
        self.dreals.popleft()
        dreal = sum(self.dreals)
        self.dlives.append(self.live - oldlive)
        self.dlives.popleft()
        dlive = sum(self.dlives)
        if dreal > dlive:
            self.dead = (1 - dlive/dreal) * 100
            self.deadstr = '{0:.2f} %'.format(self.dead)
        else:
            self.dead = 0
            self.deadstr = '%'
        
        self.reallbl.setText(self.realstr)
        self.livelbl.setText(self.livestr)
        self.deadlbl.setText(self.deadstr)
        
        # enable/disable buttons and preset boxes
        oldstate = self.active
        self.active = self.is_active()
        state_changed = (self.active != oldstate)
        
        if state_changed:
            if self.active:
                self.startbtn.setEnabled(False)
                self.stopbtn.setEnabled(True)
                
                self.rpretxt.setReadOnly(True)
                self.lpretxt.setReadOnly(True)
            else:
                self.startbtn.setEnabled(True)
                self.stopbtn.setEnabled(False)
                
                self.rpretxt.setReadOnly(False)
                self.lpretxt.setReadOnly(False)
                
        # update presets if not active
        if not self.active:
            self.rprestr = self.rpretxt.text()
            if self.rprestr == '':
                self.rpretxt.setStyleSheet(\
                    'QLineEdit { background-color: #ffffff }')
                self.rpre = 0
                self.set_real_preset(self.rpre)
            elif self.rprestr == '-' or float(self.rprestr) < 0:
                self.rpretxt.setStyleSheet(\
                    'QLineEdit { background-color: #f6989d }')
            else:
                self.rpretxt.setStyleSheet(\
                    'QLineEdit { background-color: #ffffff }')
                self.rpre = int(float(self.rprestr) * 1000)
                self.set_real_preset(self.rpre)
                
            self.lprestr = self.lpretxt.text()
            if self.lprestr == '':
                self.lpretxt.setStyleSheet(\
                    'QLineEdit { background-color: #ffffff }')
                self.lpre = 0
                self.set_live_preset(self.lpre)
            elif self.lprestr == '-' or float(self.lprestr) < 0:
                self.lpretxt.setStyleSheet(\
                    'QLineEdit { background-color: #f6989d }')
            else:
                self.lpretxt.setStyleSheet(\
                    'QLineEdit { background-color: #ffffff }')
                self.lpre = int(float(self.lprestr) * 1000)
                self.set_live_preset(self.lpre)
            
        # update gate
        self.gate = self.gatebox.currentIndex()
        self.set_gate(self.gate)
        
        # update discriminators
        self.lldstr = self.lldtxt.text()
        if self.lldstr == '':
            self.lldtxt.setStyleSheet(\
                'QLineEdit { background-color: #ffffff }')
            self.lld = 0
            self.set_lld(self.lld)
        elif self.lldstr == '-' or int(self.lldstr) < 0\
                or int(self.lldstr) > 2047:
            self.lldtxt.setStyleSheet(\
                'QLineEdit { background-color: #f6989d }')
        else:
            self.lldtxt.setStyleSheet(\
                'QLineEdit { background-color: #ffffff }')
            self.lld = int(self.lldstr)
            self.set_lld(self.lld)
            
        self.uldstr = self.uldtxt.text()
        if self.uldstr == '':
            self.uldtxt.setStyleSheet(\
                'QLineEdit { background-color: #ffffff }')
            self.uld = 0
            self.set_uld(self.uld)
        elif self.uldstr == '-' or int(self.uldstr) < 0\
                or int(self.uldstr) > 2047:
            self.uldtxt.setStyleSheet(\
                'QLineEdit { background-color: #f6989d }')
        else:
            self.uldtxt.setStyleSheet(\
                'QLineEdit { background-color: #ffffff }')
            self.uld = int(self.uldstr)
            self.set_uld(self.uld)
        
    def is_active(self):
        return self.driver.is_active(self.hdet)
        
    def start(self):
        self.driver.comm(self.hdet, 'START')
        
        self.active = self.is_active()
        if self.active:
            self.startbtn.setEnabled(False)
            self.stopbtn.setEnabled(True)
            
            self.rpretxt.setReadOnly(True)
            self.lpretxt.setReadOnly(True)
        
    def stop(self):
        self.driver.comm(self.hdet, 'STOP')
        
        self.active = self.is_active()
        if not self.active:
            self.startbtn.setEnabled(True)
            self.stopbtn.setEnabled(False)
            
            self.rpretxt.setReadOnly(False)
            self.lpretxt.setReadOnly(False)
        
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
        
    def get_gate(self):
        resp = self.driver.comm(self.hdet, 'SHOW_GATE')
        index = self.gate_index[resp[3:-1]]
        return index
        
    def get_lld(self):
        resp = self.driver.comm(self.hdet, 'SHOW_LLD')
        lld = int(resp[2:-4])
        return lld
        
    def get_uld(self):
        resp = self.driver.comm(self.hdet, 'SHOW_ULD')
        uld = int(resp[2:-4])
        return uld
        
    def set_real_preset(self, msec):
        ticks = int(msec / 20)
        self.driver.comm(self.hdet, 'SET_TRUE_PRESET {}'.format(ticks))
        
    def set_live_preset(self, msec):
        ticks = int(msec / 20)
        self.driver.comm(self.hdet, 'SET_LIVE_PRESET {}'.format(ticks))
        
    def set_gate(self, index):
        options = ['OFF', 'COINCIDENT', 'ANTICOINCIDENT']
        self.driver.comm(self.hdet, 'SET_GATE_{}'.format(options[index]))
        
    def set_lld(self, disc):
        self.driver.comm(self.hdet, 'SET_LLD {}'.format(disc))
        
    def set_uld(self, disc):
        self.driver.comm(self.hdet, 'SET_ULD {}'.format(disc))