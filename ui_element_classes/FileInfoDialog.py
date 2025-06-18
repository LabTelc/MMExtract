from PyQt5.uic import loadUiType
from utils import supportedLoadDataTypes

Ui_FileInfoDialog, QDialog = loadUiType('./ui_elements/FileInfoDialog.ui')


class FileInfoDialog(QDialog, Ui_FileInfoDialog):
    def __init__(self, parent=None, parameters=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("New images information.")
        self.cb_dtype.addItems(supportedLoadDataTypes)
        self.result = None

        self.cb_dtype.setCurrentText(parameters.dtype)
        self.sb_header.setValue(parameters.header)
        self.sb_width.setValue(parameters.width)
        self.sb_height.setValue(parameters.height)
        self.cb_ud.setChecked(parameters.flip_ud)
        self.cb_lr.setChecked(parameters.flip_lr)
        self.cb_all.setChecked(parameters.apply_queue)

        self.buttonBox.accepted.connect(self.accept)

    def accept(self):
        self.result = {
            "dtype": self.cb_dtype.currentText(),
            "width": self.sb_width.value(),
            "height": self.sb_height.value(),
            "header": self.sb_header.value(),
            "flip_lr": self.cb_lr.isChecked(),
            "flip_ud": self.cb_ud.isChecked(),
            "apply_queue": self.cb_all.isChecked(),
        }
        super().accept()
