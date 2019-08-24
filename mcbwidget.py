from mcbdriver import MCBDriver
from mcbplot import MCBPlot
from spoiler import Spoiler
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from collections import deque
from datetime import datetime

class MCBWidget(QtWidgets.QGroupBox):
    white = '#ffffff'
    red = '#ff0000'
    gray = '#cccccc'

    gate_index = {
        'OFF' : 0,
        'COIN': 1,
        'ANTI': 2
    }

    def __init__(self, mcb_driver, ndet, **kwargs):
        super().__init__(**kwargs)
        self.setObjectName('MCBBox')
        self.setStyleSheet('QGroupBox#MCBBox{' +\
            'padding-top:15px; margin-top:-15px}')
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
        self.chan_min = 8
        self.active = self.is_active()
        self.start_datetime = datetime.fromtimestamp(\
            self.driver.get_start_time(self.hdet))
        self.start_time_str = self.start_datetime.strftime('%I:%M:%S %p')
        self.start_date_str = self.start_datetime.strftime('%m/%d/%Y')

        # create label displaying MCB ID and name
        self.title = '{0:04d} {1}'.format(self.id, self.name)
        self.label = QtWidgets.QLabel(self.title)
        self.sample = QtWidgets.QLineEdit()
        self.sample.setPlaceholderText('Sample Description')

        # setup settings for storing memory
        self.settings = QtCore.QSettings('pystro', self.title)

        # load sample description settings
        if self.settings.contains('sample'):
            self.sample.setText(self.settings.value('sample'))

        # add response function for sample textbox
        def sample_change():
            if self.sample.text() == '':
                self.settings.remove('sample')
            else:
                self.settings.setValue('sample', self.sample.text())
        self.sample.textChanged.connect(sample_change)

        # get neutral button color
        self.get_neutral_color()

        # initialize sections of MCBWidget
        self.init_data_grp()
        self.init_time_grp()
        self.init_preset_grp()
        self.init_adc_grp()
        self.init_plot_grp()
        self.init_calib_grp()
        self.init_plotwidget()

        # layout widgets
        self.left_layout = QtWidgets.QVBoxLayout()
        self.right_layout = QtWidgets.QVBoxLayout()

        self.plot_layout = QtWidgets.QGridLayout()
        self.marker_layout = QtWidgets.QHBoxLayout()
        self.fit_layout = QtWidgets.QHBoxLayout()

        self.layout.addLayout(self.left_layout, 20)
        self.layout.addLayout(self.right_layout, 1)

        self.left_layout.addLayout(self.plot_layout)
        self.left_layout.addLayout(self.marker_layout)
        self.left_layout.addLayout(self.fit_layout)
        self.plot_layout.addWidget(self.label, 0, 0)
        self.plot_layout.addWidget(self.sample, 0, 1)
        self.plot_layout.addWidget(self.plot, 1, 0, 1, 2)
        self.marker_layout.addWidget(QtWidgets.QLabel('Marker: '))
        self.marker_layout.addWidget(self.chan_lbl)
        self.marker_layout.addWidget(QtWidgets.QLabel(' ('))
        self.marker_layout.addWidget(self.calib_lbl)
        self.marker_layout.addWidget(QtWidgets.QLabel(') = '))
        self.marker_layout.addWidget(self.count_lbl)
        self.marker_layout.addWidget(QtWidgets.QLabel(' Counts'))
        self.marker_layout.addWidget(QtWidgets.QWidget(), 10)
        self.fit_layout.addWidget(QtWidgets.QLabel('ROI Fit:  μ = '))
        self.fit_layout.addWidget(self.mu_chan_lbl)
        self.fit_layout.addWidget(QtWidgets.QLabel(' ('))
        self.fit_layout.addWidget(self.mu_energy_lbl)
        self.fit_layout.addWidget(QtWidgets.QLabel('),  σ = '))
        self.fit_layout.addWidget(self.sig_chan_lbl)
        self.fit_layout.addWidget(QtWidgets.QLabel(' ('))
        self.fit_layout.addWidget(self.sig_energy_lbl)
        self.fit_layout.addWidget(QtWidgets.QLabel(')'))
        self.fit_layout.addWidget(QtWidgets.QWidget(), 10)

        self.right_layout.addWidget(self.data_grp)
        self.right_layout.addWidget(self.time_grp)
        self.right_layout.addWidget(self.preset_grp)
        self.right_layout.addWidget(self.adc_grp)
        self.right_layout.addWidget(self.plot_grp)
        self.right_layout.addWidget(self.calib_grp)
        self.right_layout.addWidget(QtWidgets.QWidget(), 10)

    def get_neutral_color(self):
        # get neutral button color
        btn_color = QtWidgets.QPushButton().palette().color(\
            QtGui.QPalette.Background)
        self.neutral = '#{0:02x}{0:02x}{0:02x}'.format(\
            btn_color.red(), btn_color.green(), btn_color.blue())

    def init_plotwidget(self):
        self.counts, self.roi_mask = self.get_data()
        self.chans = self.chan_max

        # create MCB plot widget (with initial histogram and markers)
        self.plot = MCBPlot(self.chans, self.counts, self.roi_mask,\
            enableMenu=False)

        # create line info labels
        self.chan_lbl = QtWidgets.QLabel()
        self.count_lbl = QtWidgets.QLabel()
        self.calib_lbl = QtWidgets.QLabel()
        self.chan_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.count_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.calib_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.chan_lbl.setMinimumWidth(40)
        self.count_lbl.setMinimumWidth(70)
        self.calib_lbl.setMinimumWidth(80)

        # create ROI fit info labels
        self.mu_chan_lbl = QtWidgets.QLabel()
        self.mu_energy_lbl = QtWidgets.QLabel()
        self.sig_chan_lbl = QtWidgets.QLabel()
        self.sig_energy_lbl = QtWidgets.QLabel()
        self.mu_chan_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.mu_energy_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.sig_chan_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.sig_energy_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.mu_chan_lbl.setMinimumWidth(100)
        self.mu_energy_lbl.setMinimumWidth(130)
        self.sig_chan_lbl.setMinimumWidth(100)
        self.sig_energy_lbl.setMinimumWidth(130)

        # update marker and ROI fit
        self.update_marker()

        # add response function for line position change
        self.plot.line().sigPositionChanged.connect(self.update_marker)

        # add response function for ROI menu actions
        def roi_mark():
            pos = self.plot.box().pos()
            size = self.plot.box().size()
            x0 = max(int(pos.x() * self.chan_max / self.chans), 0)
            x1 = min(int((pos.x() + size.x()) * self.chan_max / self.chans),\
                self.chan_max-1)

            self.set_roi(x0, x1-x0+1)
        def roi_clear():
            pos = self.plot.box().pos()
            size = self.plot.box().size()
            x0 = max(int(pos.x() * self.chan_max / self.chans), 0)
            x1 = min(int((pos.x() + size.x()) * self.chan_max / self.chans),\
                self.chan_max-1)

            self.clear_roi(x0, x1-x0+1)
        self.plot.box().sigMark.connect(roi_mark)
        self.plot.box().sigClear.connect(roi_clear)

    def init_data_grp(self):
        # create a group for data acq buttons
        self.data_grp = QtWidgets.QGroupBox('Data Acquisition')
        self.data_layout = QtWidgets.QHBoxLayout()
        self.data_grp.setLayout(self.data_layout)

        # create data acq buttons
        self.start_btn = QtWidgets.QPushButton('')
        self.stop_btn = QtWidgets.QPushButton('')
        self.clear_btn = QtWidgets.QPushButton('')

        # add icons to data acq buttons
        self.start_btn.setIcon(QtGui.QIcon('icons/start.png'))
        self.stop_btn.setIcon(QtGui.QIcon('icons/stop.png'))
        self.clear_btn.setIcon(QtGui.QIcon('icons/clear.png'))
        self.start_btn.setIconSize(QtCore.QSize(20,20))
        self.stop_btn.setIconSize(QtCore.QSize(20,20))
        self.clear_btn.setIconSize(QtCore.QSize(20,20))

        # add response functions for data acq buttons
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.clear_btn.clicked.connect(self.clear)

        # layout data acq buttons
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
        self.start_time_lbl = QtWidgets.QLabel(self.start_time_str)
        self.start_date_lbl = QtWidgets.QLabel(self.start_date_str)
        self.real_lbl = QtWidgets.QLabel(self.real_str)
        self.live_lbl = QtWidgets.QLabel(self.live_str)
        self.dead_lbl = QtWidgets.QLabel(self.dead_str)
        self.start_time_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.start_date_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.real_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.live_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.dead_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.start_time_lbl.setMinimumWidth(50)
        self.start_date_lbl.setMinimumWidth(50)
        self.real_lbl.setMinimumWidth(50)
        self.live_lbl.setMinimumWidth(50)
        self.dead_lbl.setMinimumWidth(50)

        # layout timing labels
        self.time_layout.addWidget(QtWidgets.QLabel('Start: '), 0, 0)
        self.time_layout.addWidget(QtWidgets.QWidget(), 1, 0)
        self.time_layout.addWidget(QtWidgets.QLabel('Real: '), 2, 0)
        self.time_layout.addWidget(QtWidgets.QLabel('Live: '), 3, 0)
        self.time_layout.addWidget(QtWidgets.QLabel('Dead: '), 4, 0)
        self.time_layout.addWidget(self.start_time_lbl, 0, 1)
        self.time_layout.addWidget(self.start_date_lbl, 1, 1)
        self.time_layout.addWidget(self.real_lbl, 2, 1)
        self.time_layout.addWidget(self.live_lbl, 3, 1)
        self.time_layout.addWidget(self.dead_lbl, 4, 1)

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
        self.preset_grp = Spoiler(title='Preset Limits')
        self.preset_layout = QtWidgets.QGridLayout()

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

        # layout preset widgets
        self.preset_layout.addWidget(QtWidgets.QLabel('Real: '), 0, 0)
        self.preset_layout.addWidget(QtWidgets.QLabel('Live: '), 1, 0)
        self.preset_layout.addWidget(self.rpre_txt, 0, 1)
        self.preset_layout.addWidget(self.lpre_txt, 1, 1)
        self.preset_grp.setContentLayout(self.preset_layout)

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

        # create a group for ADC settings
        self.adc_grp = Spoiler(title='ADC Settings')
        self.adc_layout = QtWidgets.QGridLayout()

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
        self.lld_txt = QtWidgets.QLineEdit(str(self.lld))
        self.uld_txt = QtWidgets.QLineEdit(str(self.uld))
        self.lld_txt.setValidator(self.int_only)
        self.uld_txt.setValidator(self.int_only)
        self.lld_txt.setAlignment(QtCore.Qt.AlignRight)
        self.uld_txt.setAlignment(QtCore.Qt.AlignRight)
        self.lld_txt.setMinimumWidth(5)
        self.uld_txt.setMinimumWidth(5)

        # add response functions for discriminator textboxes
        def lld_change():
            lld_str = self.lld_txt.text()
            if lld_str == '':
                self.lld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.lld = 0
                self.set_lld(self.lld)
            elif lld_str == '-' or int(lld_str) < 0\
                    or int(lld_str) >= self.chan_max:
                self.lld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.lld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.lld = int(lld_str)
                self.set_lld(self.lld)
        def uld_change():
            uld_str = self.uld_txt.text()
            if uld_str == '':
                self.uld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.uld = 0
                self.set_uld(self.uld)
            elif uld_str == '-' or int(uld_str) < 0\
                    or int(uld_str) >= self.chan_max:
                self.uld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.uld_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.uld = int(uld_str)
                self.set_uld(self.uld)
        self.lld_txt.textChanged.connect(lld_change)
        self.uld_txt.textChanged.connect(uld_change)

        # layout ADC widgets
        self.adc_layout.addWidget(QtWidgets.QLabel('Gate: '), 0, 0, 1, 2)
        self.adc_layout.addWidget(QtWidgets.QLabel('Lower Disc: '), 2, 0)
        self.adc_layout.addWidget(QtWidgets.QLabel('Upper Disc: '), 3, 0)
        self.adc_layout.addWidget(self.gate_box, 1, 0, 1, 2)
        self.adc_layout.addWidget(self.lld_txt, 2, 1)
        self.adc_layout.addWidget(self.uld_txt, 3, 1)
        self.adc_grp.setContentLayout(self.adc_layout)

    def init_plot_grp(self):
        self.mode = 'Auto'

        # create a group for plot settings
        self.plot_grp = Spoiler(title='Plot Settings')
        self.plot_layout = QtWidgets.QGridLayout()

        # create plot mode buttons
        self.log_btn = QtWidgets.QPushButton('Log')
        self.auto_btn = QtWidgets.QPushButton('Auto')
        self.log_btn.setMinimumWidth(20)
        self.auto_btn.setMinimumWidth(20)
        self.disable_btn(self.auto_btn)

        # add response functions for buttons
        def log_click():
            self.mode = 'Log'
            self.disable_btn(self.log_btn)
            self.enable_btn(self.auto_btn)
            self.plot.update(self.chans, self.counts, self.roi_mask, self.mode)   
            self.popts = self.plot.fit_roi(self.get_roi(), self.calibrated,\
                self.a, self.b, self.c)
        def auto_click():
            self.mode = 'Auto'
            self.enable_btn(self.log_btn)
            self.disable_btn(self.auto_btn)
            self.plot.update(self.chans, self.counts, self.roi_mask, self.mode)
            self.popts = self.plot.fit_roi(self.get_roi(), self.calibrated,\
                self.a, self.b, self.c)
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
            self.plot.update(self.chans, self.counts, self.roi_mask, self.mode)
            self.popts = self.plot.fit_roi(self.get_roi(), self.calibrated,\
                self.a, self.b, self.c)
        self.chan_box.currentIndexChanged.connect(chan_change)

        # layout plot widgets
        self.plot_layout.addWidget(QtWidgets.QLabel('Plot Mode: '), 0, 0, 1, 2)
        self.plot_layout.addWidget(QtWidgets.QLabel('Channels: '), 2, 0)
        self.plot_layout.addWidget(self.log_btn, 1, 0)
        self.plot_layout.addWidget(self.auto_btn, 1, 1)
        self.plot_layout.addWidget(self.chan_box, 2, 1)
        self.plot_grp.setContentLayout(self.plot_layout)

    def init_calib_grp(self):
        # load fit settings if they exist
        if self.settings.contains('calibrated'):
            self.calibrated = self.settings.value('calibrated')
        else:
            self.calibrated = False
        if self.settings.contains('a'):
            self.a = self.settings.value('a')
        else:
            self.a = 0
        if self.settings.contains('b'):
            self.b = self.settings.value('b')
        else:
            self.b = 0
        if self.settings.contains('c'):
            self.c = self.settings.value('c')
        else:
            self.c = 0

        # create a group for calibrations
        self.calib_grp = Spoiler(title='Calibration')
        self.calib_layout = QtWidgets.QGridLayout()

        # create calibration textboxes
        self.chan1_txt = QtWidgets.QLineEdit()
        self.chan2_txt = QtWidgets.QLineEdit()
        self.chan3_txt = QtWidgets.QLineEdit()
        self.energy1_txt = QtWidgets.QLineEdit()
        self.energy2_txt = QtWidgets.QLineEdit()
        self.energy3_txt = QtWidgets.QLineEdit()
        self.units_txt = QtWidgets.QLineEdit()
        self.chan1_txt.setValidator(self.int_only)
        self.chan2_txt.setValidator(self.int_only)
        self.chan3_txt.setValidator(self.int_only)
        self.chan1_txt.setAlignment(QtCore.Qt.AlignRight)
        self.chan2_txt.setAlignment(QtCore.Qt.AlignRight)
        self.chan3_txt.setAlignment(QtCore.Qt.AlignRight)
        self.energy1_txt.setValidator(self.float_only)
        self.energy2_txt.setValidator(self.float_only)
        self.energy3_txt.setValidator(self.float_only)
        self.energy1_txt.setAlignment(QtCore.Qt.AlignRight)
        self.energy2_txt.setAlignment(QtCore.Qt.AlignRight)
        self.energy3_txt.setAlignment(QtCore.Qt.AlignRight)
        self.units_txt.setPlaceholderText('keV')
        self.energy1_txt.setMinimumWidth(70)
        self.energy2_txt.setMinimumWidth(70)
        self.energy3_txt.setMinimumWidth(70)

        # load calib settings
        if self.settings.contains('chan1'):
            self.chan1 = self.settings.value('chan1')
            self.chan1_txt.setText(str(self.chan1))
        else:
            self.chan1 = 0
        if self.settings.contains('chan2'):
            self.chan2 = self.settings.value('chan2')
            self.chan2_txt.setText(str(self.chan2))
        else:
            self.chan2 = 0
        if self.settings.contains('chan3'):
            self.chan3 = self.settings.value('chan3')
            self.chan3_txt.setText(str(self.chan3))
        else:
            self.chan3 = 0
        if self.settings.contains('energy1'):
            self.energy1 = self.settings.value('energy1')
            self.energy1_txt.setText('{0:.2f}'.format(self.energy1))
        else:
            self.energy1 = 0
        if self.settings.contains('energy2'):
            self.energy2 = self.settings.value('energy2')
            self.energy2_txt.setText('{0:.2f}'.format(self.energy2))
        else:
            self.energy2 = 0
        if self.settings.contains('energy3'):
            self.energy3 = self.settings.value('energy3')
            self.energy3_txt.setText('{0:.2f}'.format(self.energy3))
        else:
            self.energy3 = 0
        if self.settings.contains('units'):
            self.units = self.settings.value('units')
            self.units_txt.setText(self.settings.value('units'))
        else:
            self.units = 'keV'

        # add response functions to calibration textboxes
        def update_calib():
            calib_pts = np.array([(self.chan1, self.energy1),\
                (self.chan2, self.energy2), (self.chan3, self.energy3)])
            # ignore points where chan = 0 or energy = 0
            valid_pts = calib_pts[np.logical_and(calib_pts[:,0] > 0,\
                calib_pts[:,1] > 0), :]
            npts = valid_pts.shape[0]

            # calculate quadratic fit parameters
            try:
                if npts == 0:
                    self.calibrated = False
                    self.a = 0
                    self.b = 0
                    self.c = 0
                elif npts == 1:
                    self.calibrated = True
                    self.a = 0
                    self.b = valid_pts[0,1]/valid_pts[0,0]
                    self.c = 0
                elif npts == 2:
                    self.calibrated = True
                    self.a = 0
                    self.b = (valid_pts[1,1] - valid_pts[0,1]) /\
                        (valid_pts[1,0] - valid_pts[0,0])
                    self.c = valid_pts[0,1] - self.b * valid_pts[0,0]
                else:
                    A0 = -valid_pts[0,0]**2 + valid_pts[1,0]**2
                    B0 = -valid_pts[0,0] + valid_pts[1,0]
                    D0 = -valid_pts[0,1] + valid_pts[1,1]
                    A1 = -valid_pts[1,0]**2 + valid_pts[2,0]**2
                    B1 = -valid_pts[1,0] + valid_pts[2,0]
                    D1 = -valid_pts[1,1] + valid_pts[2,1]
                    A2 = -B1/B0 * A0 + A1
                    D2 = -B1/B0 * D0 + D1
                    self.calibrated = True
                    self.a = D2/A2
                    self.b = (D0 - A0*self.a) / B0
                    self.c = valid_pts[0,1] - self.a*valid_pts[0,0]**2 -\
                        self.b*valid_pts[0,0]
            except:
                self.calibrated = False
                self.a = 0
                self.b = 0
                self.c = 0

            self.settings.setValue('calibrated', self.calibrated)
            self.settings.setValue('a', self.a)
            self.settings.setValue('b', self.b)
            self.settings.setValue('c', self.c)

            # update marker info label
            self.update_marker()
        def chan1_change():
            chan1_str = self.chan1_txt.text()
            if chan1_str == '':
                self.chan1_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.chan1 = 0
                self.settings.remove('chan1')
            elif chan1_str == '-' or int(chan1_str) < 0\
                    or int(chan1_str) >= self.chan_max:
                self.chan1_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.chan1_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.chan1 = int(chan1_str)
                self.settings.setValue('chan1', self.chan1)
            update_calib()
        def chan2_change():
            chan2_str = self.chan2_txt.text()
            if chan2_str == '':
                self.chan2_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.chan2 = 0
                self.settings.remove('chan2')
            elif chan2_str == '-' or int(chan2_str) < 0\
                    or int(chan2_str) >= self.chan_max:
                self.chan2_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.chan2_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.chan2 = int(chan2_str)
                self.settings.setValue('chan2', self.chan2)
            update_calib()
        def chan3_change():
            chan3_str = self.chan3_txt.text()
            if chan3_str == '':
                self.chan3_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.chan3 = 0
                self.settings.remove('chan3')
            elif chan3_str == '-' or int(chan3_str) < 0\
                    or int(chan3_str) >= self.chan_max:
                self.chan3_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.chan3_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.chan3 = int(chan3_str)
                self.settings.setValue('chan3', self.chan3)
            update_calib()
        def energy1_change():
            energy1_str = self.energy1_txt.text()
            if energy1_str == '':
                self.energy1_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.energy1 = 0
                self.settings.remove('energy1')
            elif energy1_str == '-' or float(energy1_str) < 0:
                self.energy1_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.energy1_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.energy1 = float(energy1_str)
                self.settings.setValue('energy1', self.energy1)
            update_calib()
        def energy2_change():
            energy2_str = self.energy2_txt.text()
            if energy2_str == '':
                self.energy2_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.energy2 = 0
                self.settings.remove('energy2')
            elif energy2_str == '-' or float(energy2_str) < 0:
                self.energy2_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.energy2_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.energy2 = float(energy2_str)
                self.settings.setValue('energy2', self.energy2)
            update_calib()
        def energy3_change():
            energy3_str = self.energy3_txt.text()
            if energy3_str == '':
                self.energy3_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.energy3 = 0
                self.settings.remove('energy3')
            elif energy3_str == '-' or float(energy3_str) < 0:
                self.energy3_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.red))
            else:
                self.energy3_txt.setStyleSheet(\
                    'background-color: {0}'.format(self.white))
                self.energy3 = float(energy3_str)
                self.settings.setValue('energy3', self.energy3)
            update_calib()
        def units_change():
            units_str = self.units_txt.text()
            if units_str == '':
                self.units = 'keV'
                self.settings.remove('units')
            else:
                self.units = units_str
                self.settings.setValue('units', self.units)

            # update marker info label
            self.update_marker()
        self.chan1_txt.textChanged.connect(chan1_change)
        self.chan2_txt.textChanged.connect(chan2_change)
        self.chan3_txt.textChanged.connect(chan3_change)
        self.energy1_txt.textChanged.connect(energy1_change)
        self.energy2_txt.textChanged.connect(energy2_change)
        self.energy3_txt.textChanged.connect(energy3_change)
        self.units_txt.textChanged.connect(units_change)

        # layout calibration widgets
        self.calib_layout.addWidget(QtWidgets.QLabel('Channel'), 0, 0)
        self.calib_layout.addWidget(QtWidgets.QLabel('Energy/Time'), 0, 2)
        self.calib_layout.addWidget(QtWidgets.QLabel('='), 1, 1)
        self.calib_layout.addWidget(QtWidgets.QLabel('='), 2, 1)
        self.calib_layout.addWidget(QtWidgets.QLabel('='), 3, 1)
        self.calib_layout.addWidget(QtWidgets.QLabel('Units: '), 4, 0)
        self.calib_layout.addWidget(self.chan1_txt, 1, 0)
        self.calib_layout.addWidget(self.chan2_txt, 2, 0)
        self.calib_layout.addWidget(self.chan3_txt, 3, 0)
        self.calib_layout.addWidget(self.energy1_txt, 1, 2)
        self.calib_layout.addWidget(self.energy2_txt, 2, 2)
        self.calib_layout.addWidget(self.energy3_txt, 3, 2)
        self.calib_layout.addWidget(self.units_txt, 4, 1, 1, 2)
        self.calib_grp.setContentLayout(self.calib_layout)

    def update_mcb(self):
        self.counts, self.roi_mask = self.get_data()

        # update plot
        self.plot.update(self.chans, self.counts, self.roi_mask, self.mode)

        # fit ROI's
        self.popts = self.plot.fit_roi(self.get_roi(), self.calibrated, self.a,\
            self.b, self.c)

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
        self.start_datetime = datetime.fromtimestamp(\
            self.driver.get_start_time(self.hdet))
        self.start_time_str = self.start_datetime.strftime('%I:%M:%S %p')
        self.start_date_str = self.start_datetime.strftime('%m/%d/%Y')
        old_real = self.real
        self.real = self.get_real()
        self.real_str = '{0:.2f}'.format(self.real / 1000)
        old_live = self.live
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

        self.start_time_lbl.setText(self.start_time_str)
        self.start_date_lbl.setText(self.start_date_str)
        self.real_lbl.setText(self.real_str)
        self.live_lbl.setText(self.live_str)
        self.dead_lbl.setText(self.dead_str)

        # update line info label
        self.update_marker()

    def update_marker(self):
        # get marker line channel and counts
        self.line_x = int(self.plot.line().value())
        self.line_y = int(self.plot.rebin[self.line_x])

        # set channel and counts label
        self.chan_lbl.setText(str(self.line_x))
        self.count_lbl.setText(str(self.line_y))

        # if calibrated, set energy label
        if self.calibrated:
            self.calib_lbl.setText('{0:.2f} {1}'.format(self.a*self.line_x**2 +\
                self.b*self.line_x + self.c, self.units))
        else:
            self.calib_lbl.setText('uncalibrated')

        # check if marker line is in an ROI
        chan = self.line_x * self.chan_max / self.chans
        nroi = self.get_nroi(chan)

        # if in an ROI, set fit labels
        if nroi is not None:
            popt = self.popts[nroi]
            try:
                self.mu_chan_lbl.setText('{0:.2f} ± {1:.2f}'\
                    .format(popt['mu_chan_opt'], popt['mu_chan_err']))
                self.sig_chan_lbl.setText('{0:.2f} ± {1:.2f}'\
                    .format(popt['sig_chan_opt'], popt['sig_chan_err']))
            except:
                self.mu_chan_lbl.setText('could not fit')
                self.sig_chan_lbl.setText('could not fit')
            if self.calibrated:
                try:
                    self.mu_energy_lbl.setText('{0:.2f} ± {1:.2f} {2}'\
                        .format(popt['mu_energy_opt'], popt['mu_energy_err'],\
                        self.units))
                    self.sig_energy_lbl.setText('{0:.2f} ± {1:.2f} {2}'\
                        .format(popt['sig_energy_opt'], popt['sig_energy_err'],\
                        self.units))
                except:
                    self.mu_energy_lbl.setText('could not fit')
                    self.sig_energy_lbl.setText('could not fit')
            else:
                self.mu_energy_lbl.setText('uncalibrated')
                self.sig_energy_lbl.setText('uncalibrated')
        else:
            self.mu_chan_lbl.setText('')
            self.mu_energy_lbl.setText('')
            self.sig_chan_lbl.setText('')
            self.sig_energy_lbl.setText('')

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Left:
            new_pos = self.plot.line().value() - 1
            if new_pos >= 0:
                self.plot.line().setValue(new_pos)
            self.plot.box().hide()
        elif event.key() == QtCore.Qt.Key_Right:
            new_pos = self.plot.line().value() + 1
            if new_pos < self.chans:
                self.plot.line().setValue(new_pos)
            self.plot.box().hide()

    def enable_btn(self, btn):
        btn.setEnabled(True)
        btn.setStyleSheet('background-color: {0}'.format(self.neutral))

    def disable_btn(self, btn):
        btn.setEnabled(False)
        btn.setStyleSheet('background-color: {0}'.format(self.gray))

    def get_nroi(self, chan):
        rois = self.get_roi()
        count = 0
        for i in range(len(rois)):
            start_chan, num_chans = rois[i]
            if chan >= start_chan and chan < start_chan + num_chans:
                return i
        return None

    def is_active(self):
        return self.driver.is_active(self.hdet)

    def start(self):
        self.driver.comm(self.hdet, 'START')
        self.start_time = datetime.fromtimestamp(\
            self.driver.get_start_time(self.hdet))
        self.update()

    def stop(self):
        self.driver.comm(self.hdet, 'STOP')
        self.update()

    def clear(self):
        self.driver.comm(self.hdet, 'CLEAR')
        self.update()

    def get_data(self):
        return self.driver.get_data(self.hdet, 0, self.chan_max)

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

    def get_roi(self):
        rois = []
        resp = self.driver.comm(self.hdet, 'SHOW_ROI')
        while int(resp[7:12]) > 0:
            rois.append((int(resp[2:7]), int(resp[7:12])))
            resp = self.driver.comm(self.hdet, 'SHOW_NEXT')
        return rois

    def set_data(self, start_chan, num_chans=1, value=0):
        self.driver.comm(self.hdet, 'SET_DATA {}, {}, {}'.format(start_chan,\
            num_chans, value))

    def set_real(self, msec):
        ticks = int(msec / 20)
        self.driver.comm(self.hdet, 'SET_TRUE {}'.format(ticks))

    def set_live(self, msec):
        ticks = int(msec / 20)
        self.driver.comm(self.hdet, 'SET_LIVE {}'.format(ticks))

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

    def set_roi(self, start_chan, num_chans):
        self.driver.comm(self.hdet, 'SET_ROI {}, {}'.format(start_chan,\
            num_chans))

    def clear_roi(self, start_chan, num_chans):
        self.driver.comm(self.hdet, 'SET_WINDOW {}, {}'.format(start_chan,\
            num_chans))
        self.driver.comm(self.hdet, 'CLEAR_ROI')
        self.driver.comm(self.hdet, 'SET_WINDOW')