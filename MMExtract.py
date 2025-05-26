import sys
import os
import numpy as np
from queue import Queue

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog
from PyQt5.QtGui import QIcon, QTextCursor, QColor
from PyQt5.uic import loadUiType

from ui_element_classes import FileInfoDialog, VisPyCanvas, FileSaveDialog, BatchDialog
from utils import *

UI_MainWindow, QMainWindow = loadUiType('./ui_elements/MMExtract.ui')
icon_path = './ui_elements/icon_128x.png'
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class MMExtract(QMainWindow, UI_MainWindow):
    def __init__(self):
        super(MMExtract, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(icon_path))
        self.id_gen = id_generator()
        self.images = {}

        self.parameters = Parameters().from_config("utils/config.json")
        self.working_queue = Queue()
        self.worker_thread = WorkerThread(self, image_queue=self.working_queue)
        self.worker_thread.start()
        self.worker_thread.work_done.connect(self._worker_handler)

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
            getattr(self, f"canvas_{letter}").selection_changed.connect(self._handle_selection_changed)
            getattr(self, f"canvas_{letter}").save_image.connect(self._save_image_handler)
            getattr(self, f"canvas_{letter}").open_window.connect(self._window_handler)
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
                getattr(self, f"dsb_c_{letter}").valueChanged.connect(
                    lambda value, l=letter: self._handle_dsb_c(value, l))

        self.le_command.return_pressed.connect(self._handle_command)
        self.last_command = ""
        self.a_bp.triggered.connect(self.batch_processing)
        self.windows = {}

    def open_files(self, filepaths, letter):
        if letter == "r":
            return
        skip = False

        for filepath in filepaths:
            if not skip:
                dialog = FileInfoDialog(self, self.parameters)
                if dialog.exec_() == QDialog.Accepted:
                    self.parameters = self.parameters.from_parameters(dialog.result)
                    self.parameters.last_dir = os.path.dirname(filepath)
                    skip = dialog.result["apply_queue"]
                else:
                    break

            self.working_queue.put((filepath, Parameters().from_parameters(self.parameters), letter))

        self.worker_thread.wake()

    def _open_files_dialog(self):
        letter = self.sender().objectName()[-1]
        filenames, _ = QFileDialog.getOpenFileNames(self, "Load images...", self.parameters.last_dir, "All files (*.*)")
        if not filenames:
            return
        self.parameters.last_dir = os.path.dirname(filenames[0])
        self.open_files(filenames, letter)

    def _worker_handler(self, load):
        arr, filepath, letter = load
        if arr is None:
            self.log(filepath)
            return
        im_id = next(self.id_gen)
        self.images[im_id] = arr
        self.log(f"File \"{filepath}\" loaded successfully.")
        filename = os.path.basename(filepath)
        getattr(self, f"cb_files_{letter}").addItem(filename, userData=im_id)
        getattr(self, f"cb_files_{letter}").setItemData(getattr(self, f"cb_files_{letter}").count() - 1, filepath,
                                                        Qt.ToolTipRole)

    def _handle_selection_changed(self, limits):
        for l in ["a", "b", "r"]:
            getattr(self, f"canvas_{l}").set_camera_range(limits)
            if l in self.windows: self.windows[l].set_camera_range(limits)
        for l in ["a", "b"]:
            (x_min, x_max), (y_max, y_min) = np.uint16(limits)
            id_ = getattr(self, f"cb_files_{l}").currentData()
            if id_ is not None:
                m = np.mean(self.images[id_][x_min:x_max, y_min:y_max])
                getattr(self, f"l_mean_{l}").setText(f"{m:.3f}")

    def _handle_file_changed(self):
        letter = self.sender().objectName()[-1]
        img = self._get_current_image(letter)
        if img is None: return
        getattr(self, f"canvas_{letter}").show_image(img)
        getattr(self, f"range_slider_{letter}").setRange(*limits_dict_function[0](img))
        getattr(self, f"cb_auto_range_{letter}").setCurrentIndex(1)
        getattr(self, f"cb_auto_range_{letter}").setCurrentIndex(0)
        if letter in self.windows: self.windows[letter].show_image(img)

    def _get_current_image(self, letter):
        if getattr(self, f"cb_files_{letter}").count() == 0:
            return None
        im_id = getattr(self, f"cb_files_{letter}").currentData()
        if im_id is None:
            return None
        img = self.images[im_id]
        return img

    def _handle_auto_limits(self, index, letter):
        id_ = getattr(self, f"cb_files_{letter}").currentData()
        if id_ is None:
            return
        vmin, vmax = limits_dict_function[index](self.images[id_])
        getattr(self, f"canvas_{letter}").update_limits((vmin, vmax))
        if letter in self.windows: self.windows[letter].update_limits((vmin, vmax))
        getattr(self, f"range_slider_{letter}").setLowerValue(vmin)
        getattr(self, f"range_slider_{letter}").setUpperValue(vmax)

    def _handle_dsb_limits(self, value, letter, side):
        r_slider = getattr(self, f"range_slider_{letter}")
        glimits = r_slider.lowerValue(), r_slider.upperValue()
        if glimits[0] <= value <= glimits[1]:
            r_slider.blockSignals(True)
            if side == "lower":
                getattr(self, f"canvas_{letter}").set_vmin(value)
                if letter in self.windows: self.windows[letter].set_vmin(value)
                r_slider.setLowerValue(value)
            else:
                getattr(self, f"canvas_{letter}").set_vmax(value)
                if letter in self.windows: self.windows[letter].set_vmax(value)
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
                if "r" in self.windows: self.windows["r"].show_image(result)
            else:
                im_id = next(self.id_gen)
                self.images[im_id] = result
                self.cb_files_r.addItem(self.last_command, userData=im_id)
                self.cb_files_r.setCurrentIndex(self.cb_files_r.count() - 1)
        else:
            self.log(f"Result is not an array\n{result}", color="red")
            return

    def _save_image_handler(self, args):
        ftype, many = args
        letter = self.sender().objectName()[-1]
        dialog = FileSaveDialog(self)
        if dialog.exec_():
            dtype = dialog.result["dtype"]
            normalize = dialog.result["normalize"]
            filter_ = "TIFF (*.tiff)" if ftype == "tiff" else "Binary (*.bin)"
            fex = "tif" if ftype == "tiff" else "bin"
        else:
            return
        if not many:
            filename, _ = QFileDialog.getSaveFileName(self, "Save image...", self.parameters.last_dir, filter_)
            id_ = getattr(self, f"cb_files_{letter}").currentData()
            if not filename or id_ is None:
                return
            self.working_queue.put((filename, self.images[id_], (ftype, dtype, normalize)))
            self.worker_thread.wake()
        else:
            dir_path = QFileDialog.getExistingDirectory(self, "Open a directory...", self.parameters.last_dir)
            if not dir_path:
                return
            cb_files = getattr(self, f"cb_files_{letter}")
            for i in range(cb_files.count()):
                filename = os.path.basename(cb_files.itemText(i))
                filename = filename if not '.' in filename else filename[:filename.rfind('.')]
                arr = self.images[cb_files.itemData(i)]
                filename = f"{dir_path}/{filename}.{fex}"
                self.working_queue.put((filename, arr, (dtype, normalize)))
            self.worker_thread.wake()

    def _handle_dsb_c(self, value, letter):
        s_c = getattr(self, f"s_c_{letter}")
        min_, max_ = s_c.minimum(), s_c.maximum()
        if min_ <= value <= max_:
            s_c.blockSignals(True)
            getattr(self, f"s_c_{letter}").setFloatValue(value)
            s_c.blockSignals(False)
        else:
            if value < min_:
                getattr(self, f"dsb_c_{letter}").setValue(min_)
            else:
                getattr(self, f"dsb_c_{letter}").setValue(max_)

    def _window_handler(self):
        letter = self.sender().objectName()[-1]
        if letter in self.windows: return
        canvas = VisPyCanvas(size=(2000,2000))
        canvas.selection_changed.connect(self._handle_selection_changed)
        canvas.save_image.connect(self._save_image_handler)
        canvas.open_window.connect(self._window_handler)
        self.windows[letter] = canvas
        canvas.setWindowTitle(f"Image {letter.upper()}")
        canvas.show()
        canvas.closed_window.connect(lambda: self.windows.pop(letter, None))
        img = self._get_current_image(letter)
        if img is not None: canvas.show_image(img)

    def batch_processing(self):
        dialog = BatchDialog(self, self.parameters, self.last_command)
        if dialog.exec_():
            output_dir = dialog.result["output_dir"]
            if not os.path.exists(output_dir):
                return
            min_files = min(len(dialog.result["slot_a"]), len(dialog.result["slot_b"]))
            files_a = dialog.result["slot_a"][:min_files]
            files_b = dialog.result["slot_b"][:min_files]
            parameters = dialog.result["parameters"]
            ca = dialog.result["ca"]
            cb = dialog.result["cb"]
            equation = dialog.result["equation"]
            for a, b in zip(files_a, files_b):
                self.working_queue.put(((a, b), {
                    "dtype": parameters.dtype,
                    "header": parameters.header,
                    "width": parameters.width,
                    "height": parameters.height,
                    "flip_ud": parameters.flip_ud,
                    "flip_lr": parameters.flip_lr,
                    "ca": ca,
                    "cb": cb,
                    "output_dir": output_dir,
                    "ftype": dialog.result["ftype"],
                    "sdtype": dialog.result["dtype"],
                    "normalize": dialog.result["normalize"],
                }, equation))
            self.worker_thread.wake()

    def log(self, text, color="black"):
        self.te_log.setTextColor(QColor(color))
        self.te_log.append(text)
        self.te_log.moveCursor(QTextCursor.End)
        self.te_log.ensureCursorVisible()

    def closeEvent(self, event):
        self.parameters.to_config("utils/config.json")
        self.worker_thread.requestInterruption()
        self.worker_thread.wake()
        for window in self.windows:
            self.windows[window].close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main_window = MMExtract()
    main_window.show()
    app.exec_()
