from PyQt5.QtWidgets import QDoubleSpinBox

class SigFigDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sigfigs = 6
        self.setDecimals(12)

    def setSignificantFigures(self, n):
        self._sigfigs = n
        self.update()

    def textFromValue(self, value: float) -> str:
        return f"{value:.{self._sigfigs}g}"

    def valueFromText(self, text: str, **kwargs) -> float:
        try:
            return float(text)
        except ValueError:
            return self.value()
