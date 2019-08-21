from pystrowidget import PySTROWidget
from PyQt5 import QtWidgets
import pyqtgraph as pg

# set background and foreground colors
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

app = QtWidgets.QApplication([])
app.setStyle('fusion')

pystrowidget = PySTROWidget()
pystrowidget.setWindowTitle('Pystro')
# pystrowidget.showMaximized()
pystrowidget.show()

app.exec_()