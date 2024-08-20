# Duotone Image Generator

This Python application generates multiple duotone variations of an input image. It allows users to select an image file and creates 100 unique duotone versions using randomly generated color pairs.

## Features

- User-friendly image selection via a file dialog
- Generates 100 unique duotone variations
- Saves output images with descriptive filenames including color information
- Uses OpenCV for efficient image processing

## Installation

1. Clone this repository:
   ```
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

1. Run the script:
   ```
   python src/duotone_generator.py
   ```

2. A file dialog will open. Select the image you want to process.

3. The script will generate 100 duotone variations and save them in a new folder named `[original_filename]_duotone_variations` in the same directory as the input image.

4. A message box will appear when the process is complete, indicating the location of the output folder.

## Dependencies

- OpenCV (cv2)
- NumPy
- Tkinter (usually comes pre-installed with Python)

## Requirements

- Python 3.6 or higher

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
