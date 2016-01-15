import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from classes import Gui


def main():
    app = QApplication(sys.argv)
    ex = Gui.Gui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    QCoreApplication.setLibraryPaths(['C:/log-parser/Lib/site-packages/PyQt5/plugins'])
    main()