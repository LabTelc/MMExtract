from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import Qt, pyqtSignal

class DoubleSlider(QSlider):
    floatValueChanged = pyqtSignal(float, name="floatValueChanged")

    def __init__(self, parent=None, orientation=Qt.Horizontal):
        super().__init__(orientation, parent)
        self._min = 0.0
        self._max = 10.0
        self._step = 0.01
        self._multiplier = int(1 / self._step)
        self._update_slider_range()
        self.setFloatValue(1.)

        self.valueChanged.connect(self._emit_float_value)

    def setRange(self, min_val, max_val):
        self._min = min_val
        self._max = max_val
        self._update_slider_range()

    def setMaximum(self, a0):
        self._max = a0
        self._update_slider_range()

    def setMinimum(self, a0):
        self._min = a0
        self._update_slider_range()

    def setSingleStep(self, step):
        self._step = step
        self._multiplier = int(1 / step)
        self._update_slider_range()

    def _update_slider_range(self):
        super().setRange(0, int((self._max - self._min) * self._multiplier))

    def _emit_float_value(self, value):
        float_val = self._min + (value / self._multiplier)
        self.floatValueChanged.emit(float_val)

    def setFloatValue(self, float_val):
        int_val = int((float_val - self._min) * self._multiplier)
        self.setValue(int_val)

    def floatValue(self):
        return self._min + (self.value() / self._multiplier)