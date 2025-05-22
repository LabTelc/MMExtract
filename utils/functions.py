import numpy as np
import os
import re


def guess_shape(path, dtype="uint16"):
    """
    Guess the shape of the data in a file based on its size and data type.
    :param path: Path to the file
    :param dtype: Data type of the file
    :return: Tuple representing the shape of the data
    """
    file_size = os.path.getsize(path)

    match = re.search(r"\d+", dtype)
    if match:
        num_bytes = int(match.group()) // 8
        num_elements = file_size // num_bytes
    else:
        raise ValueError(f"Unsupported data type: {dtype}")

    side_length = int(np.sqrt(num_elements))
    return side_length, side_length


def validate_input(filepath, parameters):
    """
    Validate the input file based on its size and the expected shape.
    :param filepath: Path to the file
    :param parameters: Parameters object containing expected shape
    :return: True if valid, False otherwise
    """
    fex = filepath.split(".")[-1]
    if fex in ["tif", "tiff", "jpg", "jpeg", "png", "txt"]:
        return True
    try:
        size = os.path.getsize(filepath)
        match = re.search(r"\d+", parameters.dtype)
    except FileNotFoundError:
        print(f"File \"{filepath}\" not found.")
        return None
    except ValueError:
        print(f"Unsupported data type: {parameters.dtype}")
        return None
    else:
        num_bytes = int(match.group()) // 8
        size = size // num_bytes
        if size == parameters.width * parameters.height:
            return True
        else:
            return False


def id_generator():
    current_id = 0
    while True:
        yield current_id
        current_id += 1


def mask_bad_values(array):
    return array[~np.isnan(array) & ~np.isinf(array)]