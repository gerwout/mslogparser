from datetime import timezone
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class FormWidget(QWidget):

    def __init__(self, parent):
        super(FormWidget, self).__init__(parent)
        self._main_gui = parent
        self.hide()
        self.__controls()
        self.__layout()

    def __controls(self):
        self.first_date_picker = QDateTimeEdit()
        self.first_date_picker.setDisplayFormat("dd-MM-yyyy hh:mm:ss")
        self.second_date_picker = QDateTimeEdit()
        self.second_date_picker.setDisplayFormat("dd-MM-yyyy hh:mm:ss")
        self.host_names = QComboBox()
        self.host_names.addItem("-")
        self.users = QComboBox()
        self.users.addItem("-")
        self.objects = QComboBox()
        self.objects.addItem("-")
        self.types = QComboBox()
        self.types.addItem("-")
        self.full_text_search = QLineEdit()
        self.search_button = QPushButton("&Search")
        self.search_button.clicked.connect(self.handleSearch)

    def __layout(self):
        self._grid = QHBoxLayout()
        self._grid.addWidget(self.first_date_picker)
        self._grid.addWidget(self.second_date_picker)
        self._grid.addWidget(self.host_names)
        self._grid.addWidget(self.users)
        self._grid.addWidget(self.objects)
        self._grid.addWidget(self.types)
        self._grid.addWidget(self.full_text_search)
        self._grid.addWidget(self.search_button)
        self._grid.addStretch(1)
        self.setLayout(self._grid)

    def handleSearch(self):
        first_time_stamp = int(self.first_date_picker.dateTime().toPyDateTime().replace(tzinfo=timezone.utc).timestamp())
        second_time_stamp = int(self.second_date_picker.dateTime().toPyDateTime().replace(tzinfo=timezone.utc).timestamp())
        host_name = str(self.host_names.currentText())
        user = str(self.users.currentText())
        object = str(self.objects.currentText())
        type = str(self.types.currentText())
        full_text = str(self.full_text_search.text())
        self.nativeParentWidget().updateTable(first_time_stamp=first_time_stamp, second_time_stamp=second_time_stamp,
                                              host_name=host_name, user=user, object=object, type=type,
                                              full_text=full_text)
