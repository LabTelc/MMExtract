import os

from PyQt5.uic import loadUiType
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem
from PyQt5.QtGui import QIcon

from utils import Parameters, supportedSaveDataTypes
from . import FileInfoDialog, FileSaveDialog

UI_BatchDialog, QDialog = loadUiType('./ui_elements/BatchDialog.ui')


class BatchDialog(QDialog, UI_BatchDialog):
    def __init__(self, parent=None, parameters=None, equation="a-b"):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Batch processing...")
        self.parameters = parameters
        self.result = None

        self.pb_a.clicked.connect(self._add_files)
        self.pb_b.clicked.connect(self._add_files)
        self.tb_output.clicked.connect(self._pick_output_directory)

        self.dsb_ca.setValue(self.parameters.ca)
        self.dsb_cb.setValue(self.parameters.cb)
        self.le_equation.setText(equation)
        self.le_output.setText(self.parameters.last_dir)
        self.cb_dtype.addItems(supportedSaveDataTypes)

    def _add_files(self):
        letter = self.sender().objectName()[-1]

        files, _ = QFileDialog.getOpenFileNames(self, f"Select files for slot {letter.upper()}",
                                                self.parameters.last_dir)
        dialog = FileInfoDialog(self, self.parameters)
        if dialog.exec_():
            self.parameters = Parameters().from_parameters(dialog.result)
        else:
            return

        if files:
            self.parameters.last_dir = os.path.dirname(files[0])
            for file in files:
                item = QListWidgetItem(file)
                item.setIcon(QIcon(file))
                item.setData(Qt.ToolTipRole, file)
                getattr(self, f"lw_{letter}").addItem(item)
            getattr(self, f"gb_{letter}").setTitle(f"Image A ({getattr(self, f"lw_{letter}").count()} items)")

    def _pick_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select output directory",
                                                     self.parameters.last_dir)
        if directory:
            self.parameters.last_dir = directory
            self.le_output.setText(directory)

    def accept(self):
        self.result = {
            "slot_a": [self.lw_a.item(i).data(Qt.ToolTipRole) for i in range(self.lw_a.count())],
            "slot_b": [self.lw_b.item(i).data(Qt.ToolTipRole) for i in range(self.lw_b.count())],
            "output_dir": self.le_output.text(),
            "parameters": self.parameters,
            "ca": self.dsb_ca.value(),
            "cb": self.dsb_cb.value(),
            "equation": self.le_equation.text(),
            "ftype": self.cb_ftype.currentText(),
            "dtype": self.cb_dtype.currentText(),
            "normalize": self.cb_normalize.isChecked(),
        }
        super().accept()