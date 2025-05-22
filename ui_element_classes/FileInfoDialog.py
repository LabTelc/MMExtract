from PyQt5.uic import loadUiType
from utils import supportedDataTypes

Ui_FileInfoDialog, QDialog = loadUiType('./ui_elements/FileInfoDialog.ui')


class FileInfoDialog(QDialog, Ui_FileInfoDialog):
    def __init__(self, parent=None, parameters=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("New images information.")
        self.cb_dtype.addItems(supportedDataTypes)
        self.result = None

        self.cb_dtype.setCurrentText(parameters.dtype)
        self.sb_header.setValue(parameters.header)
        self.sb_width.setValue(parameters.width)
        self.sb_height.setValue(parameters.height)

        self.buttonBox.accepted.connect(self.accept)

    def accept(self):
        self.result = {
            "dtype": self.cb_dtype.currentText(),
            "width": self.sb_width.value(),
            "height": self.sb_height.value(),
            "header": self.sb_header.value(),
        }
        super().accept()
