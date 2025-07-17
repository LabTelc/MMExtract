from PyQt5.QtWidgets import QToolButton
from PyQt5.QtCore import QSize


class IconToolButton(QToolButton):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.size()
        icon_size = QSize(int(size.width() * 0.8), int(size.height() * 0.8))
        self.setIconSize(icon_size)