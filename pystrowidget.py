from mcbdriver import MCBDriver
from mcbwidget import MCBWidget
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np

class PySTROWidget(QtWidgets.QWidget):
    gray = '#cccccc'
    
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        # initialize driver and get number of MCBs
        self.driver = MCBDriver()
        self.det_max = self.driver.get_config_max()
        
        # connect with MCBs and _layout MCBWidgets
        self.mcbs = []
        for n in range(self.det_max):
            self.mcbs.append(MCBWidget(self.driver, ndet=n+1))
            self.layout.addWidget(self.mcbs[n], n+1, 0, 1, 2)
        
        # initialize master data acq buttons
        self.init_file_grp()
        self.init_data_grp()
        
        # _layout master data acq widgets
        self.layout.addWidget(self.file_grp, 0, 0)
        self.layout.addWidget(self.data_grp, 0, 1)
        
        # create QTimer to update plot
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(200)
        
    def init_file_grp(self):
        # create a group for file i/o buttons
        self.file_grp = QtWidgets.QGroupBox('Open/Save File')
        self.file_layout = QtWidgets.QHBoxLayout()
        self.file_grp.setLayout(self.file_layout)
        
        # create file i/o buttons
        self.open_btn = QtWidgets.QPushButton('')
        self.save_btn = QtWidgets.QPushButton('')
        
        # add icons to master data acq buttons
        self.open_btn.setIcon(QtGui.QIcon('icons/open.png'))
        self.save_btn.setIcon(QtGui.QIcon('icons/save.png'))
        self.open_btn.setIconSize(QtCore.QSize(30,30))
        self.save_btn.setIconSize(QtCore.QSize(30,30))
        
        # _layout master data acq buttons
        self.file_layout.addWidget(self.open_btn)
        self.file_layout.addWidget(self.save_btn)


    def init_data_grp(self):
        # create a group for master data acq buttons
        self.data_grp = QtWidgets.QGroupBox('Master Data Acquisition (All MCBs)')
        self.data_layout = QtWidgets.QHBoxLayout()
        self.data_grp.setLayout(self.data_layout)
        
        # create master data acq buttons
        self.start_btn = QtWidgets.QPushButton('')
        self.stop_btn = QtWidgets.QPushButton('')
        self.clear_btn = QtWidgets.QPushButton('')
        
        # get neutral button color
        btn_color = self.start_btn.palette().color(QtGui.QPalette.Background)
        self.neutral = '#{0:02x}{0:02x}{0:02x}'.format(\
            btn_color.red(), btn_color.green(), btn_color.blue())
        
        # add icons to master data acq buttons
        self.start_btn.setIcon(QtGui.QIcon('icons/start.png'))
        self.stop_btn.setIcon(QtGui.QIcon('icons/stop.png'))
        self.clear_btn.setIcon(QtGui.QIcon('icons/clear.png'))
        self.start_btn.setIconSize(QtCore.QSize(30,30))
        self.stop_btn.setIconSize(QtCore.QSize(30,30))
        self.clear_btn.setIconSize(QtCore.QSize(30,30))
        
        # add response functions for master data acq buttons
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.clear_btn.clicked.connect(self.clear)
        
        # _layout master data acq buttons
        self.data_layout.addWidget(self.start_btn)
        self.data_layout.addWidget(self.stop_btn)
        self.data_layout.addWidget(self.clear_btn)
        
        # enable/disable data buttons
        self.active_mcbs = [mcb.active for mcb in self.mcbs]
        self.all_active = all(self.active_mcbs)
        self.none_active = not any(self.active_mcbs)
        
        if self.all_active:
            self.disable_btn(self.start_btn)
        if self.none_active:
            self.disable_btn(self.stop_btn)
            
        self.start_btn.setStyleSheet(\
            'QLineEdit { background-color: #ffffff }')
        
    def update(self):
        # update mcb widgets
        for mcb in self.mcbs:
            mcb.update()
            
        # enable/disable data buttons
        old_active = self.active_mcbs
        self.active_mcbs = [mcb.active for mcb in self.mcbs]
        state_changed = (self.active_mcbs != old_active)
        
        if state_changed:
            self.all_active = all(self.active_mcbs)
            self.none_active = not any(self.active_mcbs)
            if self.all_active:
                self.disable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
            elif self.none_active:
                self.enable_btn(self.start_btn)
                self.disable_btn(self.stop_btn)
            else:
                self.enable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
        
    def enable_btn(self, btn):
        btn.setEnabled(True)
        btn.setStyleSheet('background-color: {0}'.format(self.neutral))
        
    def disable_btn(self, btn):
        btn.setEnabled(False)
        btn.setStyleSheet('background-color: {0}'.format(self.gray))
            
    def start(self):
        for mcb in self.mcbs:
            mcb.start()
            
        # enable/disable data buttons
        old_active = self.active_mcbs
        self.active_mcbs = [mcb.active for mcb in self.mcbs]
        state_changed = (self.active_mcbs != old_active)
        
        if state_changed:
            self.all_active = all(self.active_mcbs)
            self.none_active = not any(self.active_mcbs)
            if self.all_active:
                self.disable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
            elif self.none_active:
                self.enable_btn(self.start_btn)
                self.disable_btn(self.stop_btn)
            else:
                self.enable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
            
    def stop(self):
        for mcb in self.mcbs:
            mcb.stop()
            
        # enable/disable data buttons
        old_active = self.active_mcbs
        self.active_mcbs = [mcb.active for mcb in self.mcbs]
        state_changed = (self.active_mcbs != old_active)
        
        if state_changed:
            self.all_active = all(self.active_mcbs)
            self.none_active = not any(self.active_mcbs)
            if self.all_active:
                self.disable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
            elif self.none_active:
                self.enable_btn(self.start_btn)
                self.disable_btn(self.stop_btn)
            else:
                self.enable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
            
    def clear(self):
        for mcb in self.mcbs:
            mcb.clear()
            
        # enable/disable data buttons
        old_active = self.active_mcbs
        self.active_mcbs = [mcb.active for mcb in self.mcbs]
        state_changed = (self.active_mcbs != old_active)
        
        if state_changed:
            self.all_active = all(self.active_mcbs)
            self.none_active = not any(self.active_mcbs)
            if self.all_active:
                self.disable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)
            elif self.none_active:
                self.enable_btn(self.start_btn)
                self.disable_btn(self.stop_btn)
            else:
                self.enable_btn(self.start_btn)
                self.enable_btn(self.stop_btn)