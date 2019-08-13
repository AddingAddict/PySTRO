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

        # create a group for master control buttons
        self.btngrp = QtWidgets.QGroupBox('Data Controls')
        self.btnlayout = QtWidgets.QGridLayout()
        self.btngrp.setLayout(self.btnlayout)
        self.layout.addWidget(self.btngrp, 0, 0)
        
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
        self.btnlayout.addWidget(self.startbtn, 0, 0)
        self.btnlayout.addWidget(self.stopbtn, 0, 1)
        self.btnlayout.addWidget(self.clearbtn, 0, 2)
        
        self.mcbs = []
        for n in range(self.det_max):
            self.mcbs.append(MCBWidget(self.driver, ndet=n+1))
            self.layout.addWidget(self.mcbs[n], n+1, 0)
            
    def start(self):
        for mcb in self.mcbs:
            mcb.start()
            
    def stop(self):
        for mcb in self.mcbs:
            mcb.stop()
            
    def clear(self):
        for mcb in self.mcbs:
            mcb.clear()