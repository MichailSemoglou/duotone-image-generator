# Duotone Image Generator

A Python application that generates duotone variations of an image by blending random or explicit color pairs over the grayscale source. Accepts JPEG, PNG, and BMP input; writes a batch of lossless PNGs (100 by default) plus a `colors.csv` sidecar. Usable through file dialogs, a command-line interface, or as a Python library.

## Features

- User-friendly image selection via a file dialog
- Generates 100 duotone variations as lossless **PNG** files (count configurable)
- Filenames use **hex color codes** in RGB order (e.g. `083_2CD2B4_DC1E5A.png`) — paste directly into Figma, Illustrator, or your design system
- Produces a **`colors.csv` sidecar** listing every variation's color pair for easy reference and sharing
- Command-line mode with reproducible batches (`--seed`), configurable variation count (`--count`), and explicit color pairs (`--colors`)
- Uses OpenCV for efficient image processing

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/MichailSemoglou/duotone-image-generator.git
   cd duotone-image-generator
   ```

2. Create a virtual environment (optional but recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Interactive mode

Run the script without arguments:

```bash
python3 duotone_generator.py
```

1. A file dialog will open. Select the image you want to process, then choose an output directory.

2. The script will generate 100 duotone variations in a new folder named `[original_filename]_duotone_variations`. Each variation is a lossless PNG file named after its two hex color values (e.g. `083_2CD2B4_DC1E5A.png`). A `colors.csv` file is also written to the same folder, listing every variation's color pair.

3. A message box will appear when the process is complete, indicating the location of the output folder.

### Command-line mode

Pass the image path as an argument to run without any dialogs — suitable for scripting and headless environments:

```bash
python3 duotone_generator.py path/to/image.png [--output-dir DIR] [--count N] [--seed S] [--colors "HEX1,HEX2"]
```

- `-o, --output-dir DIR` — place the output folder under DIR instead of alongside the source image.
- `--count N` — number of random variations (default: 100).
- `--seed S` — reproduce a batch exactly by reusing its seed.
- `--colors "#2CD2B4,#DC1E5A"` — apply explicit color pairs instead of random ones; repeatable, one variation per pair. Cannot be combined with `--count` or `--seed`.

The location of the output folder is printed on completion.

### Library use

The module can be imported and used as a library, without tkinter installed:

```python
from duotone_generator import convert_to_duotone

folder, records = convert_to_duotone("photo.png", count=25, seed=42)
```

It returns the output folder path and a list of `[index, color_1_hex, color_2_hex]` records, one per variation. See the `convert_to_duotone` docstring for all parameters.

## Dependencies

- OpenCV (cv2)
- NumPy
- Tkinter (usually comes pre-installed with Python; only needed for interactive mode)

## Requirements

- Python 3.9 or higher

## Development

Install the development dependencies and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest test_duotone_generator.py
```

## Contributing

Contribute via pull request: fork the repository, create a branch, and open a pull request. Make sure the full test suite passes before submitting. For bugs or feature requests, open an issue describing the problem or the proposed change.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
