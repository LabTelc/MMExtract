from PyQt5.uic import loadUiType

from utils import supportedSaveDataTypes

Ui_FileSaveDialog, QDialog = loadUiType('./ui_elements/FileSaveDialog.ui')


class FileSaveDialog(QDialog, Ui_FileSaveDialog):
    def __init__(self, parent=None, parameters=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Choose dtype...")
        self.cb_dtype.addItems(supportedSaveDataTypes)
        self.result = None

        self.cb_dtype.currentTextChanged.connect(lambda text: self.cb_normalize.setEnabled(text == "uint16"))

    def accept(self):
        self.result = {
            "dtype": self.cb_dtype.currentText(),
            "normalize": self.cb_normalize.isChecked()
        }
        super().accept()

