from PyQt5.uic import loadUiType
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon

UI_MoverDialog, QDialog = loadUiType('./ui_elements/MoverDialog.ui')

arrow_up_path = './ui_elements/arrow_up.svg'
arrow_down_path = './ui_elements/arrow_down.svg'
arrow_left_path = './ui_elements/arrow_left.svg'
arrow_right_path = './ui_elements/arrow_right.svg'
reset_path = './ui_elements/reset.svg'


class MoverWidget(QDialog, UI_MoverDialog):
    move_image = pyqtSignal(tuple, name='move_image')
    closed_window = pyqtSignal()

    def __init__(self, parent=None, letter=None, xy_abs=(0, 0)):
        super().__init__(parent)
        self.setupUi(self)
        self.letter = letter
        self.x = xy_abs[0]
        self.y = xy_abs[1]
        self.tb_up.setIcon(QIcon(arrow_up_path))
        self.tb_down.setIcon(QIcon(arrow_down_path))
        self.tb_left.setIcon(QIcon(arrow_left_path))
        self.tb_right.setIcon(QIcon(arrow_right_path))
        self.tb_reset.setIcon(QIcon(reset_path))
        self.tb_up.clicked.connect(self._move)
        self.tb_down.clicked.connect(self._move)
        self.tb_left.clicked.connect(self._move)
        self.tb_right.clicked.connect(self._move)
        self.tb_reset.clicked.connect(self._move)

    def set_abs(self, xy_abs):
        self.x, self.y = xy_abs
        self.sb_x.setValue(self.x)
        self.sb_y.setValue(self.y)

    def _move(self):
        sender = self.sender().objectName().split('_')[-1]
        x, y = 0, 0
        if sender == 'up':
            self.x -= 1
            x = -1
        elif sender == 'down':
            self.x += 1
            x = 1
        elif sender == 'left':
            self.y -= 1
            y = -1
        elif sender == 'right':
            self.y += 1
            y = 1
        elif sender == 'reset':
            x, y = -self.x, -self.y
            self.x, self.y = 0, 0

        self.sb_x.setValue(self.x)
        self.sb_y.setValue(self.y)
        self.move_image.emit((self.letter, x, y, self.x, self.y))

    def closeEvent(self, event):
        self.closed_window.emit()
        event.accept()