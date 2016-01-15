import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from os.path import expanduser
from classes.FormWidget import FormWidget
from classes.LogParser import LogParser
from classes.SqliteStorage import SqliteStorage


class Gui(QMainWindow):
    def __init__(self):
        super(Gui, self).__init__()
        self.initUI()

    def _getExitAction(self):
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        return exitAction

    def _getOpenLogFileAction(self):
        logFileAction = QAction('Open log file', self)
        logFileAction.setShortcut('Ctrl+O')
        logFileAction.setStatusTip('Open eVision log file')
        logFileAction.triggered.connect(self._openFileDialog);

        return logFileAction

    def _openFileDialog(self):
        fileObj = QFileDialog.getOpenFileName(parent=self, caption='Open file', directory=expanduser("~"))
        if fileObj:
            file_name = str(fileObj[0])
            sql_file_name = fileObj[0] + ".sqlite"
            if os.path.isfile(sql_file_name):
                msg = "An existing database for this logfile has been found, do you want to use this one?"
                reply = QMessageBox.question(self, 'Message', msg, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    os.remove(sql_file_name)
                    self.import_log_file(file_name)
            else:
                self.import_log_file(file_name)
        self._fillTable(file_name)

    def updateTable(self, **kwargs):
        self._table.setRowCount(0)
        first_time_stamp = kwargs.get('first_time_stamp')
        second_time_stamp = kwargs.get('second_time_stamp')
        host_name = kwargs.get('host_name')
        user = kwargs.get('user')
        object = kwargs.get('object')
        type = kwargs.get('type')
        full_text = kwargs.get('full_text')
        rows = self._storage.get_log_data(first_time_stamp=first_time_stamp, second_time_stamp=second_time_stamp,
                                          host_name=host_name, user=user, object=object, type=type, full_text=full_text)
        self._handleRows(rows)

    def _handleRows(self, rows):
        count = len(rows)
        self._table.setRowCount(count)
        flags = Qt.ItemFlags()
        flags != Qt.ItemIsEditable
        flags ^= Qt.ItemIsSelectable
        for row_index, row in enumerate(rows):
            if row_index == 0:
                keys = row.keys()
                key_length = len(keys)
                self._table.setColumnCount(key_length)
                self._table.setHorizontalHeaderLabels(keys)
            for col_index, name in enumerate(keys):
                value = row[name]
                if isinstance(value, (int, float, complex)):
                    value = str(value)
                item = QTableWidgetItem(value)
                item.setFlags(flags)
                item.setForeground(QColor.fromRgb(0, 0, 0))
                self._table.setItem(row_index, col_index, item)

        self._table.resizeColumnsToContents()
        self.statusBar().showMessage(str(count) + ' results.')

    def clickTableCell(self, row, cell):
        self._table.selectRow(row)
        data = self._table.model().index(row, 7).data()
        print(data)

    # @todo: detect existince of table and replace, otherwise it will be added multiple times
    # i.e. open new log file...
    def _fillTable(self, log_file_name):
        self._table = QTableWidget()
        self._table.cellClicked.connect(self.clickTableCell)
        self._storage = SqliteStorage(log_file_name)
        rows = self._storage.get_log_data()
        self._handleRows(rows)
        min_date_time = QDateTime.fromString(self._storage.getMinDateTime(), "yyyy-MM-dd HH:mm:ss")
        max_date_time = QDateTime.fromString(self._storage.getMaxDateTime(), "yyyy-MM-dd HH:mm:ss")
        hostnames = self._storage.get_unique_hostnames()
        users = self._storage.get_unique_users()
        objects = self._storage.get_unique_objects()
        types = self._storage.get_unique_types()
        self.form_widget.first_date_picker.setMinimumDateTime(min_date_time)
        self.form_widget.first_date_picker.setDateTime(min_date_time)
        self.form_widget.second_date_picker.setMaximumDateTime(max_date_time)
        self.form_widget.second_date_picker.setDateTime(max_date_time)
        self.form_widget.host_names.addItems(hostnames)
        self.form_widget.users.addItems(users)
        self.form_widget.objects.addItems(objects)
        self.form_widget.types.addItems(types)
        self.form_widget.show()
        self._layout.addWidget(self._table)


    # @todo: does not really belong in this class
    def import_log_file(self, file_name):
         parser = LogParser()
         self.statusBar().showMessage('Importing log file...')
         parser.parse_log_file(file_name)
         self.statusBar().showMessage('Log file imported')

    def initUI(self):
        self.setWindowTitle('eVision Logparser')
        self.statusBar()
        # init menu
        exitAction = self._getExitAction()
        logFileAction = self._getOpenLogFileAction()
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(logFileAction);
        fileMenu.addAction(exitAction)
        self._layout = QVBoxLayout()
        self.form_widget = FormWidget(self)
        self._layout.addWidget(self.form_widget)
        panel = QWidget()
        panel.setLayout(self._layout)
        self.setCentralWidget(panel)
        self.show()
        self.showMaximized()