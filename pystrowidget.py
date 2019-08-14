from mcbdriver import MCBDriver
from mcbwidget import MCBWidget
from PyQt5 import QtWidgets, QtGui
import numpy as np

class PySTROWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        # initialize driver and get number of MCBs
        self.driver = MCBDriver()
        self.det_max = self.driver.get_config_max()
        
        # initialize master control buttons
        self.init_btngrp()
        
        # layout master control widgets
        self.layout.addWidget(self.btngrp, 0, 0)
        
        # connect with MCBs and layout MCBWidgets
        self.mcbs = []
        for n in range(self.det_max):
            self.mcbs.append(MCBWidget(self.driver, ndet=n+1))
            self.layout.addWidget(self.mcbs[n], n+1, 0)
            
    def init_btngrp(self):
        # create a group for master control buttons
        self.btngrp = QtWidgets.QGroupBox('Master Data Acquisition (All MCBs)')
        self.btnlayout = QtWidgets.QHBoxLayout()
        self.btngrp.setLayout(self.btnlayout)
        
        # create master control buttons
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
        
        # layout master control buttons
        self.btnlayout.addWidget(self.startbtn)
        self.btnlayout.addWidget(self.stopbtn)
        self.btnlayout.addWidget(self.clearbtn)
            
    def start(self):
        for mcb in self.mcbs:
            mcb.start()
            
    def stop(self):
        for mcb in self.mcbs:
            mcb.stop()
            
    def clear(self):
        for mcb in self.mcbs:
            mcb.clear()