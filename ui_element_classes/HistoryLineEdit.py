from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLineEdit


class HistoryLineEdit(QLineEdit):
    return_pressed = pyqtSignal(str, name="return_pressed")

    def __init__(self, parent=None):
        super(HistoryLineEdit, self).__init__(parent)
        self.history = [""]
        self.history_index = 0

    def keyPressEvent(self, event, **kwargs):
        if event.key() == Qt.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key_Down:
            self.navigate_history(1)
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            text = self.text()
            self.add_to_history(text)
            self.return_pressed.emit(text)
            self.clear()
        else:
            super(HistoryLineEdit, self).keyPressEvent(event)

    def navigate_history(self, direction):
        new_index = self.history_index + direction
        if 0 <= new_index < len(self.history):
            self.history_index = new_index
            self.setText(self.history[new_index])

    def add_to_history(self, text):
        if text:
            if text != self.history[-1]:
                self.history.append(text)
        self.history_index = len(self.history)
