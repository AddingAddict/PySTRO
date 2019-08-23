from mcbdriver import MCBDriver
from mcbwidget import MCBWidget
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import os.path

class PySTROWidget(QtWidgets.QWidget):
    gray = '#cccccc'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # initialize driver and get number of MCBs
        self.driver = MCBDriver()

        # get neutral button color
        self.get_neutral_color()

        # initialize sections of PySTROWidget
        self.init_mcb_grp()
        self.init_file_grp()
        self.init_data_grp()

        # layout widgets
        self.top_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout = QtWidgets.QVBoxLayout()

        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.bottom_layout)

        self.top_layout.addWidget(self.file_grp)
        self.top_layout.addWidget(self.data_grp)
        self.top_layout.addWidget(QtWidgets.QWidget(), 10)

        for mcb in self.mcbs:
            self.bottom_layout.addWidget(mcb)

        # create QTimers to do updates
        self.timer_mcb = QtCore.QTimer()
        self.timer_mcb.timeout.connect(self.update_mcb)
        self.timer_mcb.start(200)

        self.timer_self = QtCore.QTimer()
        self.timer_self.timeout.connect(self.update_self)
        self.timer_self.start(20)

    def get_neutral_color(self):
        # get neutral button color
        btn_color = QtWidgets.QPushButton().palette().color(\
            QtGui.QPalette.Background)
        self.neutral = '#{0:02x}{0:02x}{0:02x}'.format(\
            btn_color.red(), btn_color.green(), btn_color.blue())

    def init_mcb_grp(self):
        self.det_max = self.driver.get_config_max()

        # connect with MCBs and _layout MCBWidgets
        self.mcbs = []
        for n in range(self.det_max):
            self.mcbs.append(MCBWidget(self.driver, ndet=n+1))

    def init_file_grp(self):
        # create a group for file i/o buttons
        self.file_grp = QtWidgets.QGroupBox('Open/Save File')
        self.file_layout = QtWidgets.QGridLayout()
        self.file_grp.setLayout(self.file_layout)

        # create mcb selectrion dropdown menu
        self.mcb_box = QtWidgets.QComboBox()
        for mcb in self.mcbs:
            self.mcb_box.addItem(mcb.title)

        # create file i/o buttons
        self.open_btn = QtWidgets.QPushButton('')
        self.save_btn = QtWidgets.QPushButton('')

        # add icons to file i/o buttons
        self.open_btn.setIcon(QtGui.QIcon('icons/open.png'))
        self.save_btn.setIcon(QtGui.QIcon('icons/save.png'))
        self.open_btn.setIconSize(QtCore.QSize(40,40))
        self.save_btn.setIconSize(QtCore.QSize(40,40))

        # add response functions for file i/o buttons
        def open_click():
            nmcb = self.mcb_box.currentIndex()
            mcb = self.mcbs[nmcb]
            file_name, file_type  = QtGui.QFileDialog.getOpenFileName(self,\
                'Open File', filter='ASCII (*.Spe);;All Files (*)')
            try:
                file = open(file_name, 'r')
                lines = file.readlines()

                # get sample description
                if lines[1][:-1] != 'No sample description was entered.':
                    mcb.sample.setText(lines[1][:-1])

                # get live/real time
                live, real = map(int, lines[9].split(' '))
                mcb.set_live(live * 1000)
                mcb.set_real(real * 1000)

                # make sure channels match
                first_chan, last_chan = map(int, lines[11].split(' '))
                chan_max = mcb.chan_max
                assert last_chan+1 == chan_max,\
                    'File and MCB have different channels'

                # get data
                for i in range(chan_max):
                    mcb.set_data(start_chan=i, value=int(lines[12+i]))

                # get ROI's
                mcb.clear_roi(0, chan_max)
                nroi = int(lines[13+chan_max][:-1])
                for i in range(nroi):
                    first_chan, last_chan = map(int, lines[14+chan_max+i]\
                        .split(' '))
                    mcb.set_roi(first_chan, last_chan-first_chan+1)

                # get presets
                pre_type = lines[15+chan_max+nroi]
                if pre_type == 'Live Time\n':
                    mcb.lpre_txt.setText(lines[16+chan_max+nroi][:-1] + '.00')
                    if lines[17+chan_max+nroi][:-1] == '0':
                        mcb.rpre_txt.setText('')
                    else:
                        mcb.rpre_txt.setText(lines[17+chan_max+nroi][:-1] +\
                            '.00')
                elif pre_type == 'Real Time\n':
                    mcb.rpre_txt.setText(lines[16+chan_max+nroi][:-1] + '.00')
                    if lines[17+chan_max+nroi][:-1] == '0':
                        mcb.lpre_txt.setText('')
                    else:
                        mcb.lpre_txt.setText(lines[17+chan_max+nroi][:-1] +\
                            '.00')
                else:
                    mcb.lpre_txt.setText('')
                    mcb.rpre_txt.setText('')

                file.close()

                # update line info
                mcb.line_x = int(mcb.line.value())
                mcb.line_y = mcb.rebin[mcb.line_x]

                mcb.line_x_lbl.setText(str(mcb.line_x))
                mcb.line_y_lbl.setText(str(mcb.line_y))
            except:
                pass
        def save_click():
            nmcb = self.mcb_box.currentIndex()
            mcb = self.mcbs[nmcb]
            file_name, file_type = QtGui.QFileDialog.getSaveFileName(self,\
                'Save File', filter='ASCII (*.Spe);;All Files (*)')
            try:
                file = open(file_name, 'w')

                # write sample description
                file.write('$SPEC_ID:\n')
                sample = mcb.sample.text()
                if sample == '':
                    file.write('No sample description was entered.\n')
                else:
                    file.write(sample + '\n')
                file.write('$SPEC_REM:\n')

                # write MCB ID and name
                file.write('DET# ' + str(mcb.id) + '\n' +\
                    'DETDESC# ' + mcb.name + '\n')

                # write start date and time
                file.write(('AP# Pystro\n' +\
                    '$DATE_MEA:\n' +\
                    mcb.start_datetime.strftime('%m/%d/%Y %H:%M:%S') + '\n'))

                # write live/real time
                file.write('$MEAS_TIM:\n' +\
                    str(int(mcb.live / 1000)) + ' ' +\
                    str(int(mcb.real / 1000)) + '\n')

                # write number of channels
                file.write('$DATA:\n' +\
                    '0 ' + str(mcb.chan_max-1) + '\n')

                # write data
                for i in range(mcb.chan_max):
                    file.write(str(int(mcb.counts[i])).rjust(8) + '\n')

                # write number of ROI's
                rois = mcb.get_roi()
                file.write('$ROI:\n' +\
                    str(len(rois)) + '\n')

                # write ROI's
                for roi in rois:
                    file.write(str(roi[0]) + ' ' + str(roi[0]+roi[1]-1) + '\n')

                # write presets
                file.write('$PRESETS:\n')
                if mcb.lpre == 0 and mcb.rpre == 0:
                    file.write('None\n' +\
                    '0\n' +\
                    '0\n')
                elif mcb.rpre == 0 or mcb.lpre < mcb.rpre:
                    file.write('Live Time\n' +\
                    str(int(mcb.lpre / 1000)) + '\n' +\
                    str(int(mcb.rpre / 1000)) + '\n')
                else:
                    file.write('Real Time\n' +\
                    str(int(mcb.rpre / 1000)) + '\n' +\
                    str(int(mcb.lpre / 1000)) + '\n')

                # TODO: currently unsupported
                file.write('$ENER_FIT:\n' +\
                    '0.000000 0.000000\n' +\
                    '$MCA_CAL:\n' +\
                    '3\n' +\
                    '0.000000E+000 0.000000E+000 0.000000E+000\n' +\
                    '$SHAPE_CAL:\n' +\
                    '3\n' +\
                    '0.000000E+000 0.000000E+000 0.000000E+000\n')

                file.close()
            except:
                pass
        self.open_btn.clicked.connect(open_click)
        self.save_btn.clicked.connect(save_click)

        # layout master data acq buttons
        self.file_layout.addWidget(QtWidgets.QLabel('MCB to Open/Save:'), 0, 0)
        self.file_layout.addWidget(self.mcb_box, 1, 0)
        self.file_layout.addWidget(self.open_btn, 0, 1, 2, 1)
        self.file_layout.addWidget(self.save_btn, 0, 2, 2, 1)

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
        self.start_btn.setIconSize(QtCore.QSize(40,40))
        self.stop_btn.setIconSize(QtCore.QSize(40,40))
        self.clear_btn.setIconSize(QtCore.QSize(40,40))

        # add response functions for master data acq buttons
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.clear_btn.clicked.connect(self.clear)

        # layout master data acq buttons
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

    def update_self(self):
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

    def update_mcb(self):
        # update mcb widgets
        for mcb in self.mcbs:
            mcb.update()

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

        self.update_self()

    def clear(self):
        for mcb in self.mcbs:
            mcb.clear()

        self.update_self()