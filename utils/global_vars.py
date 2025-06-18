import json

import numpy as np
from dataclasses import dataclass
from .functions import mask_bad_values

supportedLoadDataTypes = ['int8', 'int16', 'int32', 'int64',
                      'uint8', 'uint16', 'uint32', 'uint64',
                      'float8', 'float16', 'float32', 'float64']

supportedSaveDataTypes = ["uint16", "float32"]

limits_list = ["min - max",
               "5 - 95",
               "1 - 99",
               "0.1 - 99.9",
               "0.01 - 99.99",
               "0.001 - 99.999",
               "(min+1) - (max-1)"]

limits_dict_function = {
    0: lambda x: (np.nanmin(mask_bad_values(x)), np.nanmax(mask_bad_values(x))),
    1: lambda x: (np.nanpercentile(mask_bad_values(x), 5), np.nanpercentile(mask_bad_values(x), 95)),
    2: lambda x: (np.nanpercentile(mask_bad_values(x), 1), np.nanpercentile(mask_bad_values(x), 99)),
    3: lambda x: (np.nanpercentile(mask_bad_values(x), 0.1), np.nanpercentile(mask_bad_values(x), 99.9)),
    4: lambda x: (np.nanpercentile(mask_bad_values(x), 0.01), np.nanpercentile(mask_bad_values(x), 99.99)),
    5: lambda x: (np.nanpercentile(mask_bad_values(x), 0.001), np.nanpercentile(mask_bad_values(x), 99.999)),
    6: lambda x: (np.nanmin(mask_bad_values(x)) + 1, np.nanmax(mask_bad_values(x)) - 1),
}

cmaps_list_small = ['gray', 'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'jet']


@dataclass
class Parameters:
    dtype: str = 'uint16'
    header: int = 0
    width: int = 0
    height: int = 0
    cmap: str = 'gray'
    last_dir: str = "./"
    flip_ud: bool = False
    flip_lr: bool = False
    apply_queue: bool = False
    ca: float = 1.0
    cb: float = 1.0

    def from_config(self, path):
        with open(path) as f:
            params = json.load(f)

        self.from_parameters(params)
        return self

    def to_config(self, path):
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=4)

    def from_parameters(self, params):
        self.dtype = params.get("dtype", self.dtype)
        self.header = params.get("header", self.header)
        self.width = params.get("width", self.width)
        self.height = params.get("height", self.height)
        self.cmap = params.get("cmap", self.cmap)
        self.last_dir = params.get("last_dir", self.last_dir)
        self.flip_ud = params.get("flip_ud", self.flip_ud)
        self.flip_lr = params.get("flip_lr", self.flip_lr)
        self.apply_queue = params.get("apply_queue", self.apply_queue)
        self.ca = params.get("ca", self.ca)
        self.cb = params.get("cb", self.cb)
        return self

    def get(self, parameter, *_):
        return getattr(self, parameter)

