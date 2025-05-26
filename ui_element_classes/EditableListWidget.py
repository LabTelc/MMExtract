from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtGui import QIcon


class EditableListWidget(QListWidget):
    def __init__(self, parent=None):
        super(EditableListWidget, self).__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event, **kwargs):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event, **kwargs):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event, **kwargs):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            for file in file_paths:
                item = QListWidgetItem(file)
                item.setIcon(QIcon(file))
                item.setData(Qt.ToolTipRole, file)
                self.addItem(item)
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected_indexes = self.selectedIndexes()
            for index in reversed(selected_indexes):
                self.model().removeRow(index.row())
        else:
            super().keyPressEvent(event)
