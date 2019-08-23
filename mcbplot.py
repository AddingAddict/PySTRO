from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.functions as fn
import numpy as np
import types

class MCBPlot(pg.PlotWidget):
    def __init__(self, chans, counts, roi_mask, **kwargs):
        self.rebin = counts.reshape((chans, -1)).sum(axis=1)
        roi_rebin_mask = roi_mask.reshape((chans, -1)).any(axis=1)
        self.roi_rebin = np.where(roi_rebin_mask, self.rebin, 0)

        self.view = MCBViewBox(chans, self.rebin, self.roi_rebin)
        super().__init__(viewBox=self.view, **kwargs)

        self.chans = chans
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

    def update(self, chans, counts, roi_mask, mode):
        self.rebin = counts.reshape((chans, -1)).sum(axis=1)
        roi_rebin_mask = roi_mask.reshape((chans, -1)).any(axis=1)
        self.roi_rebin = np.where(roi_rebin_mask, self.rebin, 0)

        # update plot ranges
        self.setXRange(0, chans, padding=0)
        if mode == 'Log':
            ylim = 31
        else:
            ylim = 1<<int(self.rebin.max()).bit_length()
        self.setYRange(0, ylim, padding=0)

        # update histograms
        if mode == 'Log':
            logsafe = np.maximum(1, self.rebin)
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

class MCBViewBox(pg.ViewBox):
    hist_color = (0, 191, 255)
    roi_color = (255, 63, 0)

    def __init__(self, chans, rebin, roi_rebin, **kwargs):
        super().__init__(**kwargs)
        self.contextMenu = []

        # create initial histogram
        self.hist = pg.BarGraphItem(x0=np.arange(chans), height=rebin, width=1,\
            pen=self.hist_color, brush=self.hist_color)
        self.addItem(self.hist)

        # create ROI histogram
        self.roi = pg.BarGraphItem(x0=np.arange(chans), height=roi_rebin, width=1,\
            pen=self.roi_color, brush=self.roi_color)
        self.addItem(self.roi)

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