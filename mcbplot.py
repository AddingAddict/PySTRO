from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.functions as fn
import numpy as np
import types

class MCBViewBox(pg.ViewBox):
    hist_color = (0, 191, 255)
    roi_color = (255, 0, 0)

    def __init__(self, chans, counts, roi):
        pg.ViewBox.__init__(self)
        self.contextMenu = []
        self.chans = chans
        self.ylim = 1<<int(counts.max()).bit_length()

        # create initial histogram
        self.hist = pg.BarGraphItem(x0=np.arange(chans), height=counts, width=1,\
            pen=self.hist_color, brush=self.hist_color)
        self.addItem(self.hist)

        # create ROI histogram
        roi_counts = np.where(roi, counts, 0)
        self.roi_hist = pg.BarGraphItem(x0=np.arange(chans), height=roi_counts, width=1,\
            pen=self.roi_color, brush=self.roi_color)
        self.addItem(self.roi_hist)

        # create initial marker line
        self.line = pg.InfiniteLine(pos=0, pen='k', movable=True)
        self.addItem(self.line)

        # create initial ROI box
        self.box = MCBROI(pen='k', movable=False)
        self.addItem(self.box)

        # hide ROI box when marker line is dragged
        self.line.sigDragged.connect(self.box.hide)

    def update_hist(self, chans, counts, roi, mode):
        pass

    def update_markers(self, new_chans, new_ylim):
        old_chans = self.chans
        old_ylim = self.ylim
        self.chans = new_chans
        self.ylim = new_ylim

        # update position of line
        self.line.setValue(self.line.value() * self.chans / old_chans)

        # update position of box
        if self.box.visible:
            self.box.setPos((self.box.pos().x() * self.chans / old_chans,\
                self.box.pos().y() * self.ylim / old_ylim))
            self.box.setSize((self.box.size().x() * self.chans / old_chans,\
                self.box.size().y() * self.ylim / old_ylim))

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
        pg.ROI.__init__(self, pos=(0,0), **kwargs)
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

    # override parent function to make hover highlight more bearable
    def _makePen(self):
        if self.mouseHovering:
            return fn.mkPen(255, 0, 0)
        else:
            return self.pen

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
