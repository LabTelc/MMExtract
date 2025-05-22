from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QWidget


class QRangeSlider(QWidget):
    lowerValueChanged = pyqtSignal(float, name='lowerValueChanged')
    upperValueChanged = pyqtSignal(float, name='upperValueChanged')
    rangeChanged = pyqtSignal(tuple, name='rangeChanged')

    def __init__(self, *args, **kwargs):
        super(QRangeSlider, self).__init__(*args, **kwargs)

        self._lower = 0
        self._upper = 100
        self._min = 0
        self._max = 100

        self._lower_pos = 0
        self._upper_pos = 100

        self._slider_length = 100

        self._pressed_control = None
        self._active_slider = None
        self.bad_range = False

        self.setMinimumHeight(10)
        self.setMaximumHeight(20)

    def setRange(self, min_val, max_val):
        if min_val == max_val:
            self.bad_range = True
        else:
            self.bad_range = False
        self._min = min_val
        self._max = max_val
        self._lower = min_val
        self._upper = max_val
        self.update()

    def setLowerValue(self, value):
        if self.bad_range:
            return
        self._lower = max(self._min, min(value, self._upper))
        self.update()
        self.lowerValueChanged.emit(self._lower)
        self.rangeChanged.emit((self._lower, self._upper))

    def setUpperValue(self, value):
        if self.bad_range:
            return
        self._upper = min(self._max, max(value, self._lower))
        self.update()
        self.upperValueChanged.emit(self._upper)
        self.rangeChanged.emit((self._lower, self._upper))

    def setValues(self, values):
        if self.bad_range:
            return
        self._lower = max(self._min, min(values[0], self._upper))
        self._upper = min(self._max, max(values[1], self._lower))
        self.update()
        self.lowerValueChanged.emit(self._lower)
        self.upperValueChanged.emit(self._upper)
        self.rangeChanged.emit((self._lower, self._upper))

    def lowerValue(self):
        return self._lower

    def upperValue(self):
        return self._upper

    def paintEvent(self, event, **kwargs):
        if self.bad_range:
            return
        painter = QPainter(self)
        rect = self.rect()

        # Calculate the positions of the handles
        self._lower_pos = rect.width() * (self._lower - self._min) / (self._max - self._min)
        self._upper_pos = rect.width() * (self._upper - self._min) / (self._max - self._min)

        # Get the handle color and background color from the current style
        handle_color = self.palette().color(QPalette.Highlight)
        background_color = self.palette().color(QPalette.Button)
        range_color = self.palette().color(QPalette.Highlight).lighter(150)

        # Draw the background
        painter.setPen(Qt.NoPen)
        painter.setBrush(background_color)
        painter.drawRect(rect)

        # Draw the range
        painter.setBrush(range_color)
        painter.drawRect(QRect(int(self._lower_pos), 7, int(self._upper_pos - self._lower_pos), int(rect.height()-14)))

        # Draw the handles
        handle_width = 6
        painter.setBrush(handle_color)
        painter.drawRect(QRect(int(self._lower_pos - handle_width // 2), 0, handle_width, rect.height()))
        painter.drawRect(QRect(int(self._upper_pos - handle_width // 2), 0, handle_width, rect.height()))

    def mousePressEvent(self, event, **kwargs):
        if event.buttons() & Qt.LeftButton:
            self._pressed_control = self._get_control(event.pos())
            self._active_slider = self._pressed_control
            self.update()

    def mouseMoveEvent(self, event, **kwargs):
        if self._active_slider is not None:
            pos = event.pos().x()
            value = self._min + (self._max - self._min) * pos / self.rect().width()

            if self._active_slider == "lower":
                self.setLowerValue(value)
            elif self._active_slider == "upper":
                self.setUpperValue(value)
            self.update()

    def mouseReleaseEvent(self, event, **kwargs):
        self._pressed_control = None
        self._active_slider = None
        self.update()

    def _get_control(self, pos):
        handle_width = 10
        lower_handle_rect = QRect(int(self._lower_pos - handle_width // 2), 0, handle_width, self.rect().height())
        upper_handle_rect = QRect(int(self._upper_pos - handle_width // 2), 0, handle_width, self.rect().height())

        if lower_handle_rect.contains(pos):
            return "lower"
        elif upper_handle_rect.contains(pos):
            return "upper"
        return None
