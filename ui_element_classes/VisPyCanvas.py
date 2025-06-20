import numpy as np

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu, QMainWindow
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from vispy.scene import SceneCanvas
from vispy.scene.visuals import Image, Rectangle

from utils import CustomPanZoomCamera


class VisPyCanvas(QWidget):
    selection_changed = pyqtSignal(tuple, name='image updated')
    save_image = pyqtSignal(tuple, name='save image')
    open_window = pyqtSignal(name='open window')
    closed_window = pyqtSignal(name='close window')

    def __init__(self, parent=None, size=(800, 600)):
        """
        Wrapper for VisPy canvas for controlled usage in PyQt app
        :param parent: parent QWidget
        """
        super(VisPyCanvas, self).__init__(parent)
        # PyQt
        self.canvas = SceneCanvas(parent=self, show=True, bgcolor="white", size=size)
        self.label = QLabel()
        self.label.setMaximumHeight(20)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label, 0, Qt.AlignRight)
        layout.addWidget(self.canvas.native, alignment=Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setAcceptDrops(True)
        # Events
        self.canvas.events.key_press.connect(self._on_key_press)
        self.canvas.events.mouse_move.connect(self._on_mouse_move)
        self.canvas.events.mouse_double_click.connect(self._on_mouse_double_click)
        self.canvas.events.mouse_press.connect(self._on_mouse_press)
        self.canvas.events.mouse_release.connect(self._on_mouse_release)
        self._drag_start = None
        self._drag_start_delayed = None
        # Timers
        self.doubleclick_timer = QTimer(self)
        self.doubleclick_timer.timeout.connect(self._drag_start_function)
        self.doubleclick_timer.setSingleShot(True)
        self.doubleclick_timer.setInterval(200)
        self.label_timer = QTimer(self)
        self.label_timer.timeout.connect(self._hide_label)
        self.label_timer.setSingleShot(True)
        self.label_timer.setInterval(1_000)
        # VisPy
        self.view = self.canvas.central_widget.add_view()
        self.image = Image(cmap="gray", parent=self.view.scene)
        self.image_data = np.array([[0]], np.float32)
        self.image.set_data(self.image_data)
        self.image.visible = False
        self.rect = Rectangle(center=(0, 0), width=1, height=1, color=(1, 0, 0, .01), border_color=(1, 0, 0, .75),
                              parent=self.view, border_width=2)
        self.rect.visible = False
        self.view.camera = CustomPanZoomCamera(aspect=1)
        self.view.camera.flip = (0, 1)

    def show_image(self, image: np.ndarray):
        """
        Set data of the image visual
        :param image: numpy 2D array of image data
        """
        if not self.image.visible:
            self.image.visible = True
        self.image_data = image
        self.image.set_data(self.image_data)
        f = 0
        self.selection_changed.emit(((0 + f, self.image_data.shape[1] - f), (self.image_data.shape[0] - f, 0 + f)))
        self.canvas.update()

    def update_limits(self, limits):
        """
        Set both lower and upper limit for colormap computation
        :param limits: tuple (vmin, vmax)
        """
        self.image.clim = limits

    def set_vmin(self, vmin):
        """
        Set lower limit for colormap computation
        :param vmin: Value of lower limit
        """
        self.image.clim = vmin, self.image.clim[1]

    def set_vmax(self, vmax):
        """
        Set upper limit for colormap computation
        :param vmax: Value of upper limit
        """
        self.image.clim = self.image.clim[0], vmax

    def set_cmap(self, cmap):
        """
        Changes current colormap of the current visual
        :param cmap: Colormap name or object
        """
        self.image.cmap = cmap

    def set_camera_range(self, limits):
        """
        Set camera range
        :param limits: tuple (xmin, xmax), (ymin, ymax)
        """
        self.view.camera.set_range(x=limits[0], y=limits[1])

    def dragEnterEvent(self, event, **kwargs):
        if event.mimeData().hasUrls() and isinstance(self.window(), QMainWindow):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event, **kwargs):
        if event.mimeData().hasUrls() and isinstance(self.window(), QMainWindow):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event, **kwargs):
        if event.mimeData().hasUrls() and isinstance(self.window(), QMainWindow):
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            self.window().open_files(file_paths, self.objectName()[-1])
            event.accept()
        else:
            event.ignore()

    def _canvas2image_coord(self, pos):
        tr = self.canvas.scene.node_transform(self.image)
        pos_in_img = tr.map(pos)
        return pos_in_img

    def _on_key_press(self, event):
        if event.text == "r":
            self.selection_changed.emit(((0, self.image_data.shape[1]), (self.image_data.shape[0], 0)))

    def _hide_label(self):
        self.label.setText("")
        self.label_timer.stop()

    def _on_mouse_move(self, event):
        pos = self._canvas2image_coord(event.pos)
        x, y = int(pos[0]), int(pos[1])

        if 0 <= x < self.image_data.shape[1] and 0 <= y < self.image_data.shape[0]:
            pixel_value = self.image_data[y, x]
            self.label.setText(f"row:{y:.0f}, col:{x:.0f} value:{pixel_value:.2f}")
            self.label_timer.start()
        else:
            self.label.setText("")
            self.label_timer.stop()

        if self._drag_start is None or not event.is_dragging:
            return

        start = self._drag_start
        end = event.pos

        x0, y0 = start
        x1, y1 = end
        width = max(abs(x1 - x0), 1)
        height = max(abs(y1 - y0), 1)
        center = ((x0 + x1) / 2, (y0 + y1) / 2)

        self.rect.center = center
        self.rect.width = width
        self.rect.height = height

    def _on_mouse_double_click(self, _):
        self.selection_changed.emit(((0, self.image_data.shape[1]), (self.image_data.shape[0], 0)))
        self.doubleclick_timer.stop()
        self.rect.visible = False

    def _drag_start_function(self):
        self._drag_start = self._drag_start_delayed
        self._drag_start_delayed = None
        self.rect.visible = True
        self.rect.width = 1
        self.rect.height = 1

    def _on_mouse_press(self, event):
        if self.image_data.shape[0] < 2:
            return
        if event.button == 1 and not self.doubleclick_timer.isActive():
            self.doubleclick_timer.start()
            self._drag_start_delayed = event.pos
        elif event.button == 2:
            self._show_context_menu(event)
        elif event.button == 3:
            self.open_window.emit()

    def _on_mouse_release(self, event):
        if self._drag_start is None:
            return

        start = self._canvas2image_coord(self._drag_start)
        end = self._canvas2image_coord(event.pos)

        x0, y0 = start[0], start[1]
        x1, y1 = end[0], end[1]

        xmin, xmax = sorted([x0, x1])
        ymin, ymax = sorted([y0, y1])
        self.selection_changed.emit(((xmin, xmax), (ymax, ymin)))

        self._drag_start = None
        self.rect.visible = False

    def _save_render(self):
        self.canvas.size = self.image_data.shape[1], self.image_data.shape[0]
        arr = self.canvas.render(region=(0, 0, *self.image_data.shape))
        self.set_camera_range(((0, self.image_data.shape[1]), (self.image_data.shape[0], 0)))
        self.save_image.emit(("render", arr))

    def _show_context_menu(self, event):
        menu = QMenu(self.canvas.native)
        menu.addAction("Save render (tiff)", self._save_render)
        menu.addAction("Save image (tiff)", lambda: self.save_image.emit(("tiff", False)))
        menu.addAction("Save image (bin)", lambda: self.save_image.emit(("bin", False)))
        menu.addAction("Save all images (tiff)", lambda: self.save_image.emit(("tiff", True)))
        menu.addAction("Save all images (bin)", lambda: self.save_image.emit(("bin", True)))
        menu.exec_(self.canvas.native.mapToGlobal(event.native.pos()))

    def closeEvent(self, event):
        self.closed_window.emit()
        event.accept()
