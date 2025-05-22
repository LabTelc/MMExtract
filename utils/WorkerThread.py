import queue
from PyQt5.QtCore import pyqtSignal, QThread, QMutex, QWaitCondition
import numpy as np
from PIL import Image as Image
import tifffile
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
                    self.read_file(filepath, params, slot)
                else:
                    tifffile.imwrite(filepath, to16bit_uint(params))
                    self.work_done.emit((None, f"{filepath} saved", None))

            self.wait_for_signal()

    def read_file(self, filepath, params, slot):
        fex = filepath.split('.')[-1]
        arr = None
        try:
            if fex == "bin" or fex == "pbf":
                arr = np.memmap(filepath, mode='r', dtype=params.dtype, shape=(params.height, params.width))
                arr = np.array(arr)
            elif fex == 'txt':
                with open(filepath, 'r') as f:
                    arr = np.array([[x for x in line.split()] for line in f], params.dtype)
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
        except Exception as e:
            arr = None
            filepath = f"File {filepath} could not be loaded\n{e}"
        else:
            arr = np.float32(arr)
        self.work_done.emit((arr, filepath, slot))


    def wait_for_signal(self):
        self.mutex.lock()
        self.condition.wait(self.mutex)
        self.mutex.unlock()

    def wake(self):
        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()
