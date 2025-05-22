# MMExtract

MMExtract is a Python-based GUI application for loading, visualizing, and processing image data for multi-material X-Ray. It leverages PyQt5 for the user interface and VisPy for fast image display.

## Features

- Load and manage multiple image files
- Interactive visualization with pan/zoom and colormap selection
- Customizable range and limits for image display
- Command-line style image processing with NumPy expressions
- Persistent configuration and user settings

## Requirements

- Python 3.7+
- numpy
- tifffile
- PyQt5
- VisPy

### Python Dependencies

Install all dependencies:
 - pip

```bash
pip install -r requirements.txt
```
- conda
```bash
conda install --yes --file requirements.txt
```

## Usage
1. Clone the repository
2. Run the application:
```bash
python MMExtract.py
```