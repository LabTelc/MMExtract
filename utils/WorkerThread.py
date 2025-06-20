import queue
import os
from PyQt5.QtCore import pyqtSignal, QThread, QMutex, QWaitCondition
import numpy as np
from PIL import Image as Image
import tifffile
from numpy.lib.twodim_base import fliplr

from .functions import to16bit_uint


class WorkerThread(QThread):
    work_done = pyqtSignal(tuple, name="work_done")

    def __init__(self, parent=None, image_queue: queue.Queue = None):
        super().__init__(parent=parent)
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.work_queue = image_queue

    def run(self):
        self.wait_for_signal()
        while not self.isInterruptionRequested():
            while not self.work_queue.empty():
                filepath, params, slot = self.work_queue.get()
                if slot in ["a", "b"]:
                    arr = self.read_file(filepath, params)
                    if arr is None:
                        self.work_done.emit((None, f"File {filepath} could not be loaded", None))
                    else:
                        self.work_done.emit((arr, filepath, slot))
                elif len(filepath) == 2:
                    self.compute_files(filepath, params, slot)
                else:
                    self.save_file(filepath, params, slot)
                    self.work_done.emit((None, f"{filepath} saved", None))

            self.wait_for_signal()

    @staticmethod
    def read_file(filepath, params):
        fex = filepath.split('.')[-1]
        try:
            if fex == 'txt':
                with open(filepath, 'r') as f:
                    arr = np.array([[x for x in line.split()] for line in f], params.get("dtype"))
            elif fex in ['jpg', 'jpeg', 'png']:
                arr = Image.open(filepath)
                arr = np.array(arr.convert('L'))
            elif fex in ['tiff', 'tif']:
                arr = tifffile.imread(filepath)
                if len(arr.shape) == 1:
                    arr = None
                elif len(arr.shape) > 2:
                    if arr.shape[2] > 3:
                        arr = arr[:, :, :3]
                    arr = np.dot(arr, [0.299, 0.587, 0.114])
            else:
                arr = np.memmap(filepath, mode='r', dtype=params.get("dtype"), shape=(params.get("height"), params.get("width")))
                arr = np.array(arr)
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None
        else:
            arr = np.float32(arr)
        if params.get("flip_ud"):
            arr = np.flipud(arr)
        if params.get("flip_lr"):
            arr = fliplr(arr)
        return arr

    @staticmethod
    def save_file(filepath, arr, params):
        ftype, dtype, normalize = params

        def prep_arr(filepath, arr):
            filepath = filepath if not os.path.exists(filepath) else filepath.rsplit(".", 1)[0] + "(1)." + \
                                                                     filepath.rsplit(".", 1)[1]
            if dtype == "uint16":
                if normalize:
                    arr = to16bit_uint(arr)
                else:
                    arr = np.uint16(arr)

            return filepath, arr

        if ftype == "tiff" or ftype == "render":
            filepath = filepath if filepath.endswith('.tiff') or filepath.endswith('.tif') else filepath + '.tiff'
            if ftype == "tiff":
                filepath, arr = prep_arr(filepath, arr)
            tifffile.imwrite(filepath, arr)
        else:
            filepath = filepath if filepath.endswith('.bin') else filepath + '.bin'
            filepath, arr = prep_arr(filepath, arr)
            arr.tofile(filepath)

    def compute_files(self, filepaths, params, equation):
        A = a = self.read_file(filepaths[0], params)
        B = b = self.read_file(filepaths[1], params)
        ca = params["ca"]
        cb = params["cb"]
        try:
            r = eval(equation)
        except Exception as e:
            self.work_done.emit((None, f"Error in equation: {e}", None))
            return

        if isinstance(r, np.ndarray):
            filepath = os.path.join(params["output_dir"], os.path.basename(filepaths[0]).rsplit('.', 1)[0] + "_computed")
            params = params["ftype"], params["sdtype"], params["normalize"]
            self.save_file(filepath, r, params)
            self.work_done.emit((None, f"Computed {filepath}", None))
        else:
            self.work_done.emit((None, "Equation did not return an array", None))



    def wait_for_signal(self):
        self.mutex.lock()
        self.condition.wait(self.mutex)
        self.mutex.unlock()

    def wake(self):
        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()
