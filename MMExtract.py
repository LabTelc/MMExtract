import sys
import numpy as np
from queue import Queue

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog
from PyQt5.QtGui import QIcon, QTextCursor, QColor
from PyQt5.uic import loadUiType

from ui_element_classes.FileInfoDialog import FileInfoDialog
from utils import *

UI_MainWindow, QMainWindow = loadUiType('./ui_elements/MMExtract.ui')
icon_path = './ui_elements/icon_128x.png'
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class MMExtract(QMainWindow, UI_MainWindow):
    def __init__(self):
        super(MMExtract, self).__init__()
        self.setupUi(self)
        self.icon = QIcon(icon_path)
        self.setWindowIcon(self.icon)
        self.id_gen = id_generator()
        self.images = {}

        self.parameters = Parameters()
        self.parameters.from_config("utils/config.json")
        self.loading_queue = Queue()
        self.loading_thread = ImageLoaderThread(self, image_queue=self.loading_queue)
        self.loading_thread.start()
        self.loading_thread.image_loaded.connect(self._image_loader_handler)

        for letter in ["a", "b", "r"]:
            getattr(self, f"cb_colormaps_{letter}").addItems(cmaps_list_small)
            getattr(self, f"cb_auto_range_{letter}").addItems(limits_list)
            getattr(self, f"cb_auto_range_{letter}").currentIndexChanged.connect(
                lambda index, l=letter: self._handle_auto_limits(index, l))
            getattr(self, f"range_slider_{letter}").lowerValueChanged.connect(
                lambda value, l=letter: getattr(self, f"dsb_lower_{l}").setValue(value))
            getattr(self, f"range_slider_{letter}").upperValueChanged.connect(
                lambda value, l=letter: getattr(self, f"dsb_upper_{l}").setValue(value))
            getattr(self, f"cb_colormaps_{letter}").currentTextChanged.connect(
                lambda value, l=letter: getattr(self, f"canvas_{l}").set_cmap(value))
            getattr(self, f"canvas_{letter}").selection_changed.connect(self.handle_selection_changed)
            getattr(self, f"cb_files_{letter}").currentIndexChanged.connect(self._handle_file_changed)
            getattr(self, f"dsb_lower_{letter}").valueChanged.connect(
                lambda value, l=letter: self._handle_dsb_limits(value, l, "lower"))
            getattr(self, f"dsb_upper_{letter}").valueChanged.connect(
                lambda value, l=letter: self._handle_dsb_limits(value, l, "upper"))
            if letter != "r":
                getattr(self, f"s_c_{letter}").floatValueChanged.connect(
                    lambda value, l=letter: getattr(self, f"dsb_c_{l}").setValue(value))
                getattr(self, f"tb_{letter}").clicked.connect(self._open_files_dialog)
                getattr(self, f"dsb_c_lower_{letter}").valueChanged.connect(
                    lambda value, l=letter: getattr(self, f"s_c_{l}").setMinimum(value))
                getattr(self, f"dsb_c_upper_{letter}").valueChanged.connect(
                    lambda value, l=letter: getattr(self, f"s_c_{l}").setMaximum(value))
                getattr(self, f"dsb_c_{letter}").valueChanged.connect(self._handle_command)

        self.le_command.return_pressed.connect(self._handle_command)
        self.last_command = ""

    def open_files(self, filepaths, letter):
        for filepath in filepaths:
            valid = False
            while not valid:
                self.parameters.width, self.parameters.height = guess_shape(filepath, self.parameters.dtype)
                valid = validate_input(filepath, self.parameters)
                if valid is None or valid:
                    break
                dialog = FileInfoDialog(self, self.parameters)
                dialog.setIcon(self.icon)
                if dialog.exec_() == QDialog.Accepted:
                    self.parameters.width = dialog.result["width"]
                    self.parameters.height = dialog.result["height"]
                    self.parameters.dtype = dialog.result["dtype"]
                else:
                    valid = None
                    break
            if valid is None:
                print(f"File \"{filepath}\" could not be loaded.")
            else:
                self.loading_queue.put((filepath, self.parameters, letter))

        self.loading_thread.wake()

    def _open_files_dialog(self):
        letter = self.sender().objectName()[-1]
        filenames, _ = QFileDialog.getOpenFileNames(self, "Load images...", self.parameters.last_dir, "All files (*.*)")
        if not filenames:
            return
        self.parameters.last_dir = filenames[0][:filenames[0].rfind("/")]
        self.open_files(filenames, letter)

    def _image_loader_handler(self, load):
        arr, filepath, letter = load
        if arr is None:
            print(f"File \"{filepath}\" could not be loaded.")
            return
        im_id = next(self.id_gen)
        self.images[im_id] = arr

        getattr(self, f"cb_files_{letter}").addItem(filepath, userData=im_id)

    def handle_selection_changed(self, limits):
        for l in ["a", "b", "r"]:
            getattr(self, f"canvas_{l}").set_camera_range(limits)
        for l in ["a", "b"]:
            (x_min, x_max), (y_max, y_min) = np.uint16(limits)
            id_ = getattr(self, f"cb_files_{l}").currentData()
            if id_ is not None:
                m = np.mean(self.images[id_][x_min:x_max, y_min:y_max])
                getattr(self, f"l_mean_{l}").setText(f"{m:.3f}")

    def _handle_file_changed(self):
        letter = self.sender().objectName()[-1]
        if getattr(self, f"cb_files_{letter}").count() == 0:
            return
        im_id = getattr(self, f"cb_files_{letter}").currentData()
        if im_id is None:
            return
        img = self.images[im_id]
        getattr(self, f"canvas_{letter}").show_image(img)
        getattr(self, f"range_slider_{letter}").setRange(*limits_dict_function[0](img))
        getattr(self, f"cb_auto_range_{letter}").setCurrentIndex(1)
        getattr(self, f"cb_auto_range_{letter}").setCurrentIndex(0)

    def _handle_auto_limits(self, index, letter):
        id_ = getattr(self, f"cb_files_{letter}").currentData()
        if id_ is None:
            return
        vmin, vmax = limits_dict_function[index](self.images[id_])
        getattr(self, f"canvas_{letter}").update_limits((vmin, vmax))
        getattr(self, f"range_slider_{letter}").setLowerValue(vmin)
        getattr(self, f"range_slider_{letter}").setUpperValue(vmax)

    def _handle_dsb_limits(self, value, letter, side):
        r_slider = getattr(self, f"range_slider_{letter}")
        glimits = r_slider.lowerValue(), r_slider.upperValue()
        if glimits[0] <= value <= glimits[1]:
            r_slider.blockSignals(True)
            if side == "lower":
                getattr(self, f"canvas_{letter}").set_vmin(value)
                r_slider.setLowerValue(value)
            else:
                getattr(self, f"canvas_{letter}").set_vmax(value)
                r_slider.setUpperValue(value)
            r_slider.blockSignals(False)
        else:
            if side == "lower":
                getattr(self, f"dsb_lower_{letter}").setValue(glimits[0])
            else:
                getattr(self, f"dsb_upper_{letter}").setValue(glimits[1])

    def _handle_command(self):
        sender = self.sender().objectName()
        if sender == "le_command":
            self.last_command = self.le_command.text()
            self.le_command.clear()

        if self.last_command == "":
            return

        a = A = self.images.get(self.cb_files_a.currentData(), None)
        b = B = self.images.get(self.cb_files_b.currentData(), None)
        r = R = self.images.get(self.cb_files_r.currentData(), None)
        ca = self.dsb_c_a.value()
        cb = self.dsb_c_b.value()
        log = np.log
        canvas = self.canvas_a

        try:
            result = eval(self.last_command)
        except Exception as e:
            self.log(f"Error in command: {self.last_command}\n{e}", color="red")
            return

        if isinstance(result, np.ndarray):
            if sender != "le_command":
                id_r = self.cb_files_r.currentData()
                if id_r is None:
                    return
                self.images[id_r] = result
                self.canvas_r.show_image(result)
            else:
                im_id = next(self.id_gen)
                self.images[im_id] = result
                self.cb_files_r.addItem(self.last_command, userData=im_id)
                self.cb_files_r.setCurrentIndex(self.cb_files_r.count() - 1)
        else:
            self.log(f"Result is not an array\n{result}", color="red")
            return

    def log(self, text, color="black"):
        self.te_log.setTextColor(QColor(color))
        self.te_log.append(text)
        self.te_log.moveCursor(QTextCursor.End)
        self.te_log.ensureCursorVisible()

    def closeEvent(self, event):
        self.parameters.to_config("utils/config.json")
        self.loading_thread.requestInterruption()
        self.loading_thread.wake()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main_window = MMExtract()

    main_window.show()
    app.exec_()
