from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from os.path import expanduser
from classes.FormWidget import FormWidget
from classes.LogParser import LogParser
from classes.SqliteStorage import SqliteStorage
import csv
import io
import os

class Gui(QMainWindow):
    def __init__(self):
        super(Gui, self).__init__()
        self.initUI()

    def _getExitAction(self):
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self._quitApplication)

        return exitAction

    def _quitApplication(self):
        if self.logFileAction.isEnabled():
            self._storage.close_db()
        qApp.quit()

    def _getOpenLogFileAction(self):
        logFileAction = QAction('Add log file(s)', self)
        logFileAction.setShortcut('Ctrl+A')
        logFileAction.setStatusTip('Add eVision log file(s)')
        logFileAction.setDisabled(True)
        logFileAction.triggered.connect(self._openFileDialog);

        return logFileAction

    def _getCreateDBAction(self):
        createDBAction = QAction('Create new database', self)
        createDBAction.setShortcut('Ctrl+N')
        createDBAction.setStatusTip('Create new database')
        createDBAction.triggered.connect(self._createNewDBDialog);

        return createDBAction

    def _getOpenDBAction(self):
        openDBAction = QAction('Open database', self)
        openDBAction.setShortcut('Ctrl+O')
        openDBAction.setStatusTip('Open database')
        openDBAction.triggered.connect(self._openDBDialog);

        return openDBAction


    def _createNewDBDialog(self):
        fileObj = QFileDialog.getSaveFileName(self, 'Create new database', expanduser("~"), filter='*.sqlite')
        if fileObj and fileObj[0] != "":
            self.logFileAction.setDisabled(False)
            file_name = str(fileObj[0])
            if file_name.endswith(".sqlite"):
                file_name = file_name[:-7]

            if os.path.isfile(file_name + ".sqlite"):
                msg_box = QMessageBox()
                msg_box.setText("The database "+ file_name + ".sqlite already exists!")
                res = msg_box.exec_()
                if res == QMessageBox.Ok:
                    self._createNewDBDialog()
            else:
                try:
                    if self._storage:
                        self._storage.close_db()
                except AttributeError:
                    pass

                self._storage = SqliteStorage(file_name, create=True)
                self.statusBar().showMessage('Database '+file_name+".sqlite created.")
                try:
                    if self._table:
                        self._table.clear()
                        self._table.setRowCount(0)
                        self._table.hide()
                        self._message_window.hide()
                except AttributeError:
                    pass


    def _openDBDialog(self):
        fileObj = QFileDialog.getOpenFileName(parent=self, caption='Open file', directory=expanduser("~"),
                                              filter='*.sqlite')
        if fileObj and fileObj[0] != "":
            file_name = str(fileObj[0])
            try:
                if self._storage:
                    self._storage.close_db()
            except AttributeError:
                pass
            self._storage = SqliteStorage(file_name)
            self.logFileAction.setDisabled(False)
            self.statusBar().showMessage('Database '+file_name+" opened.")
            self._fillTable()

    def _openFileDialog(self):
        fileObj = QFileDialog.getOpenFileNames(parent=self, caption='Open file', directory=expanduser("~"))

        if fileObj and fileObj[0] != "":
            self._storage.drop_fulltext_index()
            self._storage.drop_indexes()
            parser = LogParser(storage=self._storage)
            for file_name in fileObj[0]:
                self.statusBar().showMessage('Importing log file ' + file_name + '...')
                QApplication.processEvents()
                parser.parse_log_file(str(file_name))

            self._storage.commit_changes()
            self.statusBar().showMessage('Busy creating indexes...')
            self._storage.update_fulltext_index()
            self._storage.create_indexes()
            self._fillTable()

    def updateTable(self, **kwargs):
        self._table.clear()
        self._table.setRowCount(0)
        first_time_stamp = kwargs.get('first_time_stamp')
        second_time_stamp = kwargs.get('second_time_stamp')
        host_name = kwargs.get('host_name')
        pid = kwargs.get('pid')
        trans_id = kwargs.get('trans_id')
        user = kwargs.get('user')
        object = kwargs.get('object')
        type = kwargs.get('type')
        full_text = kwargs.get('full_text')
        rows = self._storage.get_log_data(first_time_stamp=first_time_stamp, second_time_stamp=second_time_stamp,
                                          host_name=host_name, pid=pid, trans_id=trans_id, user=user, object=object,
                                          type=type, full_text=full_text)
        self._handleRows(rows)

    def _handleRows(self, rows):
        count = len(rows)
        self._table.setRowCount(count)
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
                item.setForeground(QColor.fromRgb(0, 0, 0))
                self._table.setItem(row_index, col_index, item)

        self._table.resizeColumnsToContents()
        self.statusBar().showMessage(str(count) + ' results.')

    def showLogMessage(self):
        items = self._table.selectedItems()
        count = len(items)
        if count != 0:
            row = items[count - 1].row()
            data = self._table.model().index(row, 7).data()
            self._message_window.setText(data)

    def _handleExport(self):
        items = self._table.selectedItems()
        output = io.StringIO()
        header = ["date_time", "host_name", "pid", "transaction_id", "user", "object", "type", "message"]
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        for item in items:
            row = item.row()
            date_time = self._table.model().index(row, 0).data()
            host_name = self._table.model().index(row, 1).data()
            pid = self._table.model().index(row, 2).data()
            trans_id = self._table.model().index(row, 3).data()
            user = self._table.model().index(row, 4).data()
            object = self._table.model().index(row, 5).data()
            type = self._table.model().index(row, 6).data()
            message = self._table.model().index(row, 7).data()
            csv_data = [date_time, host_name, pid, trans_id, user, object, type, message]
            writer.writerow(csv_data)
        csv_content = output.getvalue()
        fileObj = QFileDialog.getSaveFileName(self, "Save csv file", "", ".csv")
        if fileObj and fileObj[0] != "":
            file_name = fileObj[0] + fileObj[1]
            csv_file = open(file_name, "w")
            csv_file.write(csv_content)
            csv_file.close()
            self.statusBar().showMessage(file_name + ' saved.')




    def _createRightClickMenu(self, pos):
        #row = self._table.rowAt(pos.y())
        #column = self._table.columnAt(pos.x())
        menu = QMenu(self._table)
        exportAction = QAction("&Export as csv", None)
        exportAction.triggered.connect(self._handleExport)
        menu.addAction(exportAction)
        menu.exec_(self._table.viewport().mapToGlobal(pos))


    def _fillTable(self):
        rows = self._storage.get_log_data()
        if rows:
            try:
                if self._table:
                    self._layout.removeWidget(self._table)
                    self._layout.removeWidget(self._message_window)
                    self._table = None
            except AttributeError:
                pass

            self._table = QTableWidget()
            self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self._table.setContextMenuPolicy(Qt.CustomContextMenu)
            self._table.customContextMenuRequested.connect(self._createRightClickMenu)
            self._table.itemSelectionChanged.connect(self.showLogMessage)
            self._message_window = QTextEdit()
            self._message_window.setReadOnly(True)
            self._handleRows(rows)
            min_date_time = QDateTime.fromString(self._storage.getMinDateTime(), "yyyy-MM-dd HH:mm:ss")
            max_date_time = QDateTime.fromString(self._storage.getMaxDateTime(), "yyyy-MM-dd HH:mm:ss")
            hostnames = self._storage.get_unique_hostnames()
            pids = self._storage.get_unique_process_ids()
            trans_ids = self._storage.get_unique_transaction_ids()
            users = self._storage.get_unique_users()
            objects = self._storage.get_unique_objects()
            types = self._storage.get_unique_types()
            self.form_widget.first_date_picker.setMinimumDateTime(min_date_time)
            self.form_widget.first_date_picker.setDateTime(min_date_time)
            self.form_widget.second_date_picker.setMaximumDateTime(max_date_time)
            self.form_widget.second_date_picker.setDateTime(max_date_time)
            self.form_widget.host_names.addItems(hostnames)
            self.form_widget.pids.addItems(pids)
            self.form_widget.trans_ids.addItems(trans_ids)
            self.form_widget.users.addItems(users)
            self.form_widget.objects.addItems(objects)
            self.form_widget.types.addItems(types)
            self.form_widget.show()
            self._layout.addWidget(self._table)
            self._layout.addWidget(self._message_window)

    def initUI(self):
        self.setWindowTitle('Microsoft Logparser')
        self.statusBar()
        # init menu
        self.exitAction = self._getExitAction()
        self.logFileAction = self._getOpenLogFileAction()
        self.createDBAction = self._getCreateDBAction()
        self.openDBAction = self._getOpenDBAction()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.createDBAction)
        fileMenu.addAction(self.openDBAction)
        fileMenu.addAction(self.logFileAction)
        fileMenu.addAction(self.exitAction)
        self._layout = QVBoxLayout()
        self._layout.setAlignment(Qt.AlignTop)
        self.form_widget = FormWidget(self)
        self._layout.addWidget(self.form_widget)
        panel = QWidget()
        panel.setLayout(self._layout)
        self.setCentralWidget(panel)
        self.show()
        self.showMaximized()