from mcbdriver import MCBDriver
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from collections import deque

class MCBWidget(QtWidgets.QWidget):
    white = '#ffffff'
    red = '#ff0000'
    gray = '#cccccc'
    
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
        self.chan_max = self.driver.get_det_length(self.hdet)
        self.chan_min = 256
        self.active = self.is_active()
        
        # create label displaying MCB ID and name
        self.label = QtWidgets.QLabel('{0:04d} {1}'.format(self.id,\
            self.name))
        
        # initialize sections of MCBWidget
        self.init_plotwidget()
        self.init_data_grp()
        self.init_time_grp()
        self.init_preset_grp()
        self.init_adc_grp()
        self.init_plot_grp()
        
        # _layout widgets
        self.left_layout = QtWidgets.QVBoxLayout()
        self.mid_layout = QtWidgets.QVBoxLayout()
        self.right_layout = QtWidgets.QVBoxLayout()
        
        self.layout.addLayout(self.left_layout, 20)
        self.layout.addLayout(self.mid_layout, 1)
        self.layout.addLayout(self.right_layout, 1)
        
        self.left_layout.addWidget(self.label)
        self.left_layout.addWidget(self.plot)
        
        self.mid_layout.addWidget(self.data_grp)
        self.mid_layout.addWidget(self.time_grp)
        self.mid_layout.addWidget(self.preset_grp)
        self.mid_layout.addWidget(QtWidgets.QWidget(), 10)
        
        self.right_layout.addWidget(self.adc_grp)
        self.right_layout.addWidget(self.plot_grp)
        self.right_layout.addWidget(QtWidgets.QWidget(), 10)
        
    def init_plotwidget(self):
        self.counts = self.driver.get_data(self.hdet)
        self.chans = self.chan_max
        
        # create plot window
        self.plot = pg.PlotWidget()
        self.plot.setXRange(0, self.chans-1, padding=0)
        self.plot.setYRange(0, 1<<int(self.counts.max()).bit_length(),\
            padding=0)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.setMinimumWidth(1024)
        
        # create initial histogram
        self.chans = self.chan_max
        self.hist = pg.BarGraphItem(x=np.arange(self.chans),\
            height=self.counts, width=1, pen='b', brush='b')
        self.plot.addItem(self.hist)
        
    def init_data_grp(self):
        # create a group for data acq buttons
        self.data_grp = QtWidgets.QGroupBox('Data Acquisition')
        self.data_layout = QtWidgets.QHBoxLayout()
        self.data_grp.setLayout(self.data_layout)
        
        # create data acq buttons
        self.start_btn = QtWidgets.QPushButton('')
        self.stop_btn = QtWidgets.QPushButton('')
        self.clear_btn = QtWidgets.QPushButton('')
        
        # get neutral button color
        btn_color = self.start_btn.palette().color(QtGui.QPalette.Background)
        self.neutral = '#{0:02x}{0:02x}{0:02x}'.format(\
            btn_color.red(), btn_color.green(), btn_color.blue())
        
        # add icons to data acq buttons
        self.start_btn.setIcon(QtGui.QIcon('icons/start.png'))
        self.stop_btn.setIcon(QtGui.QIcon('icons/stop.png'))
        self.clear_btn.setIcon(QtGui.QIcon('icons/clear.png'))
        self.start_btn.setIconSize(QtCore.QSize(25,25))
        self.stop_btn.setIconSize(QtCore.QSize(25,25))
        self.clear_btn.setIconSize(QtCore.QSize(25,25))
        
        # add response functions for data acq buttons
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.clear_btn.clicked.connect(self.clear)
        
        # _layout data acq buttons
        self.data_layout.addWidget(self.start_btn)
        self.data_layout.addWidget(self.stop_btn)
        self.data_layout.addWidget(self.clear_btn)
        
        # enable/disable buttons
        if self.active:
            self.disable_btn(self.start_btn)
            self.enable_btn(self.stop_btn)
        else:
            self.enable_btn(self.start_btn)
            self.disable_btn(self.stop_btn)
        
    def init_time_grp(self):
        self.real = self.get_real()
        self.real_str = '{0:.2f}'.format(self.real / 1000)
        self.live = self.get_live()
        self.live_str = '{0:.2f}'.format(self.live / 1000)
        self.dead = 0
        self.dead_str = '%'
        self.dreals = deque([0]*4)
        self.dlives = deque([0]*4)
        
        # create a group for timing information
        self.time_grp = QtWidgets.QGroupBox('Timing')
        self.time_layout = QtWidgets.QGridLayout()
        self.time_grp.setLayout(self.time_layout)
        
        # create timing labels
        self.real_lbl = QtWidgets.QLabel(self.real_str)
        self.live_lbl = QtWidgets.QLabel(self.live_str)
        self.dead_lbl = QtWidgets.QLabel(self.dead_str)
        self.real_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.live_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.dead_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.real_lbl.setMinimumWidth(50)
        self.live_lbl.setMinimumWidth(50)
        self.dead_lbl.setMinimumWidth(50)
        
        # _layout timing labels
        self.time_layout.addWidget(QtWidgets.QLabel('Real: '), 0, 0)
        self.time_layout.addWidget(QtWidgets.QLabel('Live: '), 1, 0)
        self.time_layout.addWidget(QtWidgets.QLabel('Dead: '), 2, 0)
        self.time_layout.addWidget(self.real_lbl, 0, 1)
        self.time_layout.addWidget(self.live_lbl, 1, 1)
        self.time_layout.addWidget(self.dead_lbl, 2, 1)
        
    def init_preset_grp(self):
        self.rpre = self.get_real_preset()
        if self.rpre > 0:
            self.rpre_str = '{0:.2f}'.format(self.rpre / 1000)
        else:
            self.rpre_str = ''
        self.lpre = self.get_live_preset()
        if self.lpre > 0:
            self.lpre_str = '{0:.2f}'.format(self.lpre / 1000)
        else:
            self.lpre_str = ''
            
        # create a group for preset limits
        self.preset_grp = QtWidgets.QGroupBox('Preset Limits')
        self.preset_layout = QtWidgets.QGridLayout()
        self.preset_grp.setLayout(self.preset_layout)
        
        # create preset textboxes
        self.rpre_txt = QtWidgets.QLineEdit(self.rpre_str)
        self.lpre_txt = QtWidgets.QLineEdit(self.lpre_str)
        self.rpre_txt.setValidator(self.float_only)
        self.lpre_txt.setValidator(self.float_only)
        self.rpre_txt.setAlignment(QtCore.Qt.AlignRight)
        self.lpre_txt.setAlignment(QtCore.Qt.AlignRight)
        self.rpre_txt.setMinimumWidth(50)
        self.lpre_txt.setMinimumWidth(50)
        
        # add response functions to preset textboxes
        def rpre_changed():
            if not self.active:
                self.rpre_str = self.rpre_txt.text()
                if self.rpre_str == '':
                    self.rpre_txt.setStyleSheet(\
                        'background-color: {0}'.format(self.white))
                    self.rpre = 0
                    self.set_real_preset(self.rpre)
                elif self.rpre_str == '-' or float(self.rpre_str) < 0:
                    self.rpre_txt.setStyleSheet(\
                        'background-color: {0}'.format(self.red))
                else:
                    self.rpre_txt.setStyleSheet(\
                        'background-color: {0}'.format(self.white))
                    self.rpre = int(float(self.rpre_str) * 1000)
                    self.set_real_preset(self.rpre)
        def lpre_changed():
            if not self.active:
                self.lpre_str = self.lpre_txt.text()
                if self.lpre_str == '':
                    self.lpre_txt.setStyleSheet(\
                        'background-color: {0}'.format(self.white))
                    self.lpre = 0
                    self.set_live_preset(self.lpre)
                elif self.lpre_str == '-' or float(self.lpre_str) < 0:
                    self.lpre_txt.setStyleSheet(\
                        'background-color: {0}'.format(self.red))
                else:
                    self.lpre_txt.setStyleSheet(\
                        'background-color: {0}'.format(self.white))
                    self.lpre = int(float(self.lpre_str) * 1000)
                    self.set_live_preset(self.lpre)
        self.rpre_txt.textChanged.connect(rpre_changed)
        self.lpre_txt.textChanged.connect(lpre_changed)
        
        # _layout preset widgets
        self.preset_layout.addWidget(QtWidgets.QLabel('Real: '), 0, 0)
        self.preset_layout.addWidget(QtWidgets.QLabel('Live: '), 1, 0)
        self.preset_layout.addWidget(self.rpre_txt, 0, 1)
        self.preset_layout.addWidget(self.lpre_txt, 1, 1)
        
        # enable/disable presets
        if self.active:
            self.rpre_txt.setReadOnly(True)
            self.lpre_txt.setReadOnly(True)
        else:
            self.rpre_txt.setReadOnly(False)
            self.lpre_txt.setReadOnly(False)
        
    def init_adc_grp(self):
        self.gate = self.get_gate()
        self.lld = self.get_lld()
        self.uld = self.get_uld()
        self.lld_str = str(self.lld)
        self.uld_str = str(self.uld)
        
        # create a group for ADC settings
        self.adc_grp = QtWidgets.QGroupBox('ADC Settings')
        self.adc_layout = QtWidgets.QGridLayout()
        self.adc_grp.setLayout(self.adc_layout)
        
        # create gate dropdown menu
        self.gate_box = QtWidgets.QComboBox()
        for option in ['Off', 'Coincidence', 'Anticoincidence']:
            self.gate_box.addItem(option)
        self.gate_box.setCurrentIndex(self.gate)
        
        # add response function for gate menu
        def gate_change():
            self.gate = self.gate_box.currentIndex()
            self.set_gate(self.gate)
        self.gate_box.currentIndexChanged.connect(gate_change)
        
        # create discriminator textboxes
        self.lld_txt = QtWidgets.QLineEdit(self.lld_str)
        self.uld_txt = QtWidgets.QLineEdit(self.uld_str)
        self.lld_txt.setValidator(self.int_only)
        self.uld_txt.setValidator(self.int_only)
        self.lld_txt.setAlignment(QtCore.Qt.AlignRight)
        self.uld_txt.setAlignment(QtCore.Qt.AlignRight)
        self.lld_txt.setMinimumWidth(5)
        self.uld_txt.setMinimumWidth(5)
        
        # add response functions for discriminator textboxes
        def lld_change():
            self.lld_str = self.lld_txt.text()
            if self.lld_str == '':
                self.lld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.lld = 0
                self.set_lld(self.lld)
            elif self.lld_str == '-' or int(self.lld_str) < 0\
                    or int(self.lld_str) > self.chan_max:
                self.lld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.lld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.lld = int(self.lld_str)
                self.set_lld(self.lld)
        def uld_change():
            self.uld_str = self.uld_txt.text()
            if self.uld_str == '':
                self.uld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.uld = 0
                self.set_uld(self.uld)
            elif self.uld_str == '-' or int(self.uld_str) < 0\
                    or int(self.uld_str) > self.chan_max:
                self.uld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.uld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.uld = int(self.uld_str)
                self.set_uld(self.uld)
        self.lld_txt.textChanged.connect(lld_change)
        self.uld_txt.textChanged.connect(uld_change)
        
        # _layout ADC widgets
        self.adc_layout.addWidget(QtWidgets.QLabel('Gate: '), 0, 0, 1, 2)
        self.adc_layout.addWidget(QtWidgets.QLabel('Lower Disc: '), 2, 0)
        self.adc_layout.addWidget(QtWidgets.QLabel('Upper Disc: '), 3, 0)
        self.adc_layout.addWidget(self.gate_box, 1, 0, 1, 2)
        self.adc_layout.addWidget(self.lld_txt, 2, 1)
        self.adc_layout.addWidget(self.uld_txt, 3, 1)
        
    def init_plot_grp(self):
        self.mode = 'Auto'
        
        # create a group for plot settings
        self.plot_grp = QtWidgets.QGroupBox('Plot Settings')
        self.plot_layout = QtWidgets.QGridLayout()
        self.plot_grp.setLayout(self.plot_layout)
        
        # create plot mode buttons
        self.log_btn = QtWidgets.QPushButton('Log')
        self.auto_btn = QtWidgets.QPushButton('Auto')
        self.log_btn.setMinimumWidth(20)
        self.auto_btn.setMinimumWidth(20)
        self.auto_btn.setEnabled(False)
        
        # add response functions for buttons
        def log_click():
            self.mode = 'Log'
            self.disable_btn(self.log_btn)
            self.enable_btn(self.auto_btn)
            
            self.plot.setYRange(0, 31, padding=0)
            logsafe = np.maximum(1, self.rebin)
            self.hist.setOpts(x=np.arange(self.chans), height=np.log2(logsafe))
        def auto_click():
            self.mode = 'Auto'
            self.enable_btn(self.log_btn)
            self.disable_btn(self.auto_btn)
            
            self.plot.setYRange(0, 1<<int(self.rebin.max()).bit_length(),\
                padding=0)
            self.hist.setOpts(x=np.arange(self.chans), height=self.rebin)
        self.log_btn.clicked.connect(log_click)
        self.auto_btn.clicked.connect(auto_click)
        
        # create rebinning dropdown menu
        self.chan_box = QtWidgets.QComboBox()
        self.chan_box.setEditable(True)
        self.chan_box.lineEdit().setReadOnly(True)
        self.chan_box.lineEdit().setAlignment(QtCore.Qt.AlignRight)
        chans = self.chan_max
        n = 0
        while chans >= self.chan_min:
            self.chan_box.addItem(str(int(chans)))
            self.chan_box.setItemData(n, QtCore.Qt.AlignRight,\
                QtCore.Qt.TextAlignmentRole)
            chans /= 2
            n += 1
            
        # add response function for rebinning menu
        def chan_change():
            self.chans = int(self.chan_max / (1<<self.chan_box.currentIndex()))
            
            self.plot.setXRange(0, self.chans-1, padding=0)
            self.rebin = self.counts.reshape((self.chans, -1)).sum(axis=1)
            if self.mode == 'Log':
                self.plot.setYRange(0, 31, padding=0)
                logsafe = np.maximum(1, self.rebin)
                self.hist.setOpts(x=np.arange(self.chans),\
                    height=np.log2(logsafe))
            else:
                self.plot.setYRange(0, 1<<int(self.rebin.max()).bit_length(),\
                    padding=0)
                self.hist.setOpts(x=np.arange(self.chans), height=self.rebin)
        self.chan_box.currentIndexChanged.connect(chan_change)
        
        # _layout plot widgets
        self.plot_layout.addWidget(QtWidgets.QLabel('Plot Mode: '), 0, 0, 1, 2)
        self.plot_layout.addWidget(QtWidgets.QLabel('Channels: '), 2, 0)
        self.plot_layout.addWidget(self.log_btn, 1, 0)
        self.plot_layout.addWidget(self.auto_btn, 1, 1)
        self.plot_layout.addWidget(self.chan_box, 2, 1)
        
    def update(self):
        # update plot
        self.counts = self.driver.get_data(self.hdet)
        self.rebin = self.counts.reshape((self.chans, -1)).sum(axis=1)
        
        self.plot.setXRange(0, self.chans-1, padding=0)
        if self.mode == 'Log':
            self.plot.setYRange(0, 31, padding=0)
            logsafe = np.maximum(1, self.rebin)
            self.hist.setOpts(x=np.arange(self.chans), height=np.log2(logsafe))
        else:
            self.plot.setYRange(0, 1<<int(self.rebin.max()).bit_length(),\
                padding=0)
            self.hist.setOpts(x=np.arange(self.chans), height=self.rebin)
        
        # enable/disable data buttons and preset boxes
        old_state = self.active
        self.active = self.is_active()
        state_changed = (self.active != old_state)
        
        if state_changed:
            if self.active:
                self.disable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
                
                self.rpre_txt.setReadOnly(True)
                self.lpre_txt.setReadOnly(True)
            else:
                self.enable_btn(self.start_btn)
                self.disable_btn(self.stop_btn)
                
                self.rpre_txt.setReadOnly(False)
                self.lpre_txt.setReadOnly(False)
            
        # update timing
        old_real = self.real
        old_live = self.live
        
        self.real = self.get_real()
        self.real_str = '{0:.2f}'.format(self.real / 1000)
        self.live = self.get_live()
        self.live_str = '{0:.2f}'.format(self.live / 1000)
        
        if self.active:
            self.dreals.append(self.real - old_real)
            self.dreals.popleft()
            dreal = sum(self.dreals)
            self.dlives.append(self.live - old_live)
            self.dlives.popleft()
            dlive = sum(self.dlives)
            if dreal > dlive:
                self.dead = (1 - dlive/dreal) * 100
                self.dead_str = '{0:.2f} %'.format(self.dead)
            else:
                self.dead = 0
                self.dead_str = '%'
        else:
            self.dead = 0
            self.dead_str = '%'
        
        self.real_lbl.setText(self.real_str)
        self.live_lbl.setText(self.live_str)
        self.dead_lbl.setText(self.dead_str)
        
    def enable_btn(self, btn):
        btn.setEnabled(True)
        btn.setStyleSheet('background-color: {0}'.format(self.neutral))
        
    def disable_btn(self, btn):
        btn.setEnabled(False)
        btn.setStyleSheet('background-color: {0}'.format(self.gray))
        
    def is_active(self):
        return self.driver.is_active(self.hdet)
        
    def start(self):
        self.driver.comm(self.hdet, 'START')
        self.update()
        
    def stop(self):
        self.driver.comm(self.hdet, 'STOP')
        self.update()
        
    def clear(self):
        self.driver.comm(self.hdet, 'CLEAR')
        self.update()
        
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