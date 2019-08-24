from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.functions as fn
import numpy as np
from scipy.optimize import curve_fit
import types

class MCBPlot(pg.PlotWidget):
    def __init__(self, chan_max, counts, roi_mask, **kwargs):
        self.rebin = counts
        self.roi_rebin_mask = roi_mask
        self.roi_rebin = np.where(self.roi_rebin_mask, self.rebin, 0)

        self.view = MCBViewBox(chan_max, self.rebin, self.roi_rebin)
        super().__init__(viewBox=self.view, **kwargs)

        self.chan_max = chan_max
        self.chans = chan_max
        self.ylim = 1<<int(counts.max()).bit_length()

        self.setMouseEnabled(False, False)
        self.hideAxis('bottom')
        self.hideAxis('left')
        self.setMinimumWidth(1024)
        self.setXRange(0, self.chans, padding=0)
        self.setYRange(0, self.ylim, padding=0)

    def line(self):
        return self.view.line

    def box(self):
        return self.view.box

    def hist(self):
        return self.view.hist

    def roi(self):
        return self.view.roi

    def fit(self):
        return self.view.fit

    def fit_roi(self, rois, calibrated, a, b, c):
        roi_chans_full = np.arange(self.chans)[self.roi_rebin_mask] + 0.5
        fit_counts_full = np.array([])
        popts = []

        for roi in rois:
            # get starting channel and number of channels of rebinned ROI
            start_chan, num_chans = roi
            final_chan = int((start_chan+num_chans-1) * self.chans /\
                self.chan_max)
            start_chan = int(start_chan * self.chans / self.chan_max)
            num_chans = final_chan - start_chan + 1

            # create arrays of ROI channels, energies, and counts
            roi_chans = (start_chan + np.arange(num_chans))
            real_chans = roi_chans * self.chan_max / self.chans
            roi_mid_chan = int(start_chan + num_chans / 2)
            real_mid_chan = int((real_chans[0] + real_chans[-1]) / 2)
            real_num_chans = num_chans * self.chan_max / self.chans
            if calibrated:
                roi_energies = a*roi_chans**2 + b*roi_chans + c
                real_energies = roi_energies * self.chan_max /self.chans
                real_mid_energy = (real_energies[0] + real_energies[-1]) / 2
                real_num_energies = real_energies[-1] - real_energies[0]
            roi_counts = self.rebin[roi_chans]

            # perform fit to both channels and energies
            try:
                chan_popt, chan_pcov = curve_fit(self.gauss_bg, real_chans,\
                    roi_counts, sigma=np.sqrt(np.maximum(roi_counts,1)),\
                    absolute_sigma=True, p0=(self.rebin[roi_mid_chan],\
                    real_mid_chan, real_num_chans/2, 0, 0))
                chan_perr = np.sqrt(np.diag(chan_pcov))
            except:
                chan_popt = [None]*5
                chan_perr = [None]*5
            if calibrated:
                try:
                    energy_popt, energy_pcov = curve_fit(self.gauss_bg,\
                        real_energies, roi_counts,\
                        sigma=np.sqrt(np.maximum(roi_counts,1)),\
                        absolute_sigma=True, p0=(self.rebin[roi_mid_chan],\
                        real_mid_energy, real_num_energies/2, 0, 0))
                    energy_perr = np.sqrt(np.diag(energy_pcov))
                except:
                    energy_popt = [None]*5
                    energy_perr = [None]*5
                popts.append({
                    'mu_chan_opt': chan_popt[1],
                    'mu_chan_err': chan_perr[1],
                    'sig_chan_opt': chan_popt[2],
                    'sig_chan_err': chan_perr[2],
                    'mu_energy_opt': energy_popt[1],
                    'mu_energy_err': energy_perr[1],
                    'sig_energy_opt': energy_popt[2],
                    'sig_energy_err': energy_perr[2]
                })
            else:
                popts.append({
                    'mu_chan_opt': chan_popt[1],
                    'mu_chan_err': chan_perr[1],
                    'sig_chan_opt': chan_popt[2],
                    'sig_chan_err': chan_perr[2]
                })
            try:
                fit_counts = self.gauss_bg(real_chans, *chan_popt)
            except:
                fit_counts = roi_counts
            fit_counts_full = np.concatenate([fit_counts_full, fit_counts])

        # plot fit points
        if self.mode == 'Log':
            logsafe = np.maximum(fit_counts_full, 1)
            self.fit().setData(x=roi_chans_full, y=np.log2(logsafe))
        else:
            self.fit().setData(x=roi_chans_full, y=fit_counts_full)

        return popts

    def update(self, chans, counts, roi_mask, mode):
        self.rebin = counts.reshape((chans, -1)).sum(axis=1)
        self.roi_rebin_mask = roi_mask.reshape((chans, -1)).any(axis=1)
        self.roi_rebin = np.where(self.roi_rebin_mask, self.rebin, 0)

        # update plot ranges
        self.setXRange(0, chans, padding=0)
        self.mode = mode
        if self.mode == 'Log':
            ylim = 31
        else:
            ylim = 1<<int(self.rebin.max()).bit_length()
        self.setYRange(0, ylim, padding=0)

        # update histograms
        if self.mode == 'Log':
            logsafe = np.maximum(self.rebin, 1)
            roi_logsafe = np.maximum(1, self.roi_rebin)
            self.hist().setOpts(x0=np.arange(chans), height=np.log2(logsafe))
            self.roi().setOpts(x0=np.arange(chans), height=np.log2(roi_logsafe))
        else:
            self.hist().setOpts(x0=np.arange(chans), height=self.rebin)
            self.roi().setOpts(x0=np.arange(chans), height=self.roi_rebin)

        old_chans = self.chans
        old_ylim = self.ylim
        self.chans = chans
        self.ylim = ylim

        # update position of line
        self.line().setValue(self.line().value() * self.chans / old_chans)

        # update position of box
        if self.box().visible:
            self.box().setPos((self.box().pos().x() * self.chans / old_chans,\
                self.box().pos().y() * self.ylim / old_ylim))
            self.box().setSize((self.box().size().x() * self.chans / old_chans,\
                self.box().size().y() * self.ylim / old_ylim))

    def gauss_bg(self, x, A, mu, sig, m, b):
        return A * np.exp( - (x - mu)**2 / (2 * sig**2) ) + m*x + b

class MCBViewBox(pg.ViewBox):
    hist_color = (0, 191, 255)
    roi_color = (255, 63, 0)

    def __init__(self, chan_max, rebin, roi_rebin, **kwargs):
        super().__init__(**kwargs)
        self.contextMenu = []

        # create initial histogram
        self.hist = pg.BarGraphItem(x0=np.arange(chan_max), height=rebin,\
            width=1, pen=self.hist_color, brush=self.hist_color)
        self.addItem(self.hist)

        # create ROI histogram
        self.roi = pg.BarGraphItem(x0=np.arange(chan_max), height=roi_rebin,\
            width=1, pen=self.roi_color, brush=self.roi_color)
        self.addItem(self.roi)

        # create roi fit scatterplot
        self.fit = MCBScatter(pen='k')
        self.addItem(self.fit)

        # create initial marker line
        self.line = pg.InfiniteLine(pos=0, pen='k', movable=True)
        self.addItem(self.line)

        # create initial ROI box
        self.box = MCBROI(pen='k', movable=False)
        self.addItem(self.box)

        # hide ROI box when marker line is dragged
        self.line.sigDragged.connect(self.box.hide)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            # move line to click location
            pos = self.hist.mapFromScene(ev.scenePos())
            self.line.setValue(pos)

            # hide ROI box
            self.box.hide()

            ev.accept()
        else:
            ev.ignore()

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            # move ROI box to corners of dragged region
            corner0 = self.hist.mapFromScene(ev.buttonDownScenePos())
            corner1 = self.hist.mapFromScene(ev.scenePos())
            self.box.show(corner0, corner1)

            # move line to midpoint of ROI box
            self.line.setValue((corner1.x() + corner0.x())/2)

            ev.accept()
        else:
            ev.ignore()

class MCBROI(pg.ROI):
    sigMark = QtCore.Signal(object)
    sigClear = QtCore.Signal(object)

    def __init__(self, **kwargs):
        super().__init__(pos=(0,0), **kwargs)
        self.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self.visible = False
        self.hide()

        # create mark/clear ROI menu
        self.menu = QtGui.QMenu()
        self.menu.setTitle('Mark/Clear ROI')

        # create menu actions
        self.mark = QtGui.QAction('Mark ROI', self.menu)
        self.clear = QtGui.QAction('Clear ROI', self.menu)

        # add response functions for menu actions
        self.mark.triggered.connect(self.sigMark.emit)
        self.clear.triggered.connect(self.sigClear.emit)

        # add menu actions to menu
        self.menu.addAction(self.mark)
        self.menu.addAction(self.clear)

    def show(self, corner0, corner1):
        self.setPos((min(corner0.x(), corner1.x()),\
            min(corner0.y(), corner1.y())))
        self.setSize((abs(corner1.x() - corner0.x()),\
            abs(corner1.y() - corner0.y())))
        self.visible = True

    def hide(self):
        self.setPos((0,-1))
        self.setSize((0,0))
        self.visible = False

    # override parent function so left/mid click is ignored
    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton,\
                    QtCore.Qt.MidButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and\
                        ev.acceptClicks(btn):
                    hover=True
        if hover:
            self.setMouseHover(True)
            self.sigHoverEvent.emit(self)
            ev.acceptClicks(QtCore.Qt.RightButton)
        else:
            self.setMouseHover(False)

    # override parent function to open custom menu
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            pos = ev.screenPos()
            self.menu.popup(QtCore.QPoint(pos.x(), pos.y()))

            ev.accept()
        else:
            ev.ignore()

class MCBScatter(pg.ScatterPlotItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # override parent function to ignore clicks
    def mouseClickEvent(self, ev):
        ev.ignore()