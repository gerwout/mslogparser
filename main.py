import sys
from PyQt5.QtWidgets import *
from classes import Gui

def main():
    app = QApplication(sys.argv)
    ex = Gui.Gui()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()