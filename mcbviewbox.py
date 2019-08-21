from PyQt5 import QtCore
import pyqtgraph as pg
import numpy as np

class MCBViewBox(pg.ViewBox):
    hist_color = (0, 191, 255)

    def __init__(self, chans):
        pg.ViewBox.__init__(self)
        self.chans = chans

    def init_hist(self, chans, rebin):
        self.hist = pg.BarGraphItem(x0=np.arange(chans), height=rebin, width=1,\
            pen=self.hist_color, brush=self.hist_color)
        self.addItem(self.hist)

    def init_line(self):
        self.line = pg.InfiniteLine(pos=0, pen='k', movable=True)
        self.addItem(self.line)

        self.line.sigDragged.connect(self.hide_box)

    def init_box(self):
        self.box = pg.ROI(pos=(0,-1), size=(0,0), pen='k', movable=False)
        self.addItem(self.box)

    def set_chans(self, new_chans):
        old_chans = self.chans
        self.chans = new_chans

        # update position of line
        self.line.setValue(self.view.line.value() * self.chans / old_chans)

    def hide_box(self):
        self.box.setPos((0,-1))
        self.box.setSize((0,0))

    def mouseClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            event.accept()

            # move line to click location
            pos = self.hist.mapFromScene(event.scenePos())
            self.line.setValue(pos)

            # hide ROI box
            self.hide_box()
        else:
            event.ignore()

    def mouseDragEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            event.accept()

            # move ROI box to corners of dragged region
            corner0 = self.hist.mapFromScene(event.buttonDownScenePos())
            corner1 = self.hist.mapFromScene(event.scenePos())
            self.box.setPos((min(corner0.x(), corner1.x()),\
                min(corner0.y(), corner1.y())))
            self.box.setSize((abs(corner1.x() - corner0.x()),\
                abs(corner1.y() - corner0.y())))

            # move line to midpoint of ROI box
            self.line.setValue((corner1.x() + corner0.x())/2)
        else:
            event.ignore()