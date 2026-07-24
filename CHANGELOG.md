# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-07-24

### Added

- Command-line interface: `python3 duotone_generator.py <image> [--output-dir DIR]` generates variations without any GUI dialogs, enabling headless and scripted use.
- `convert_to_duotone` now returns a tuple of the output folder path and the color records.
- Reproducible and configurable batches: `convert_to_duotone` accepts `count`, `seed`, and `colors` parameters, exposed via the CLI flags `--count`, `--seed`, and `--colors`. A seeded run regenerates an identical batch; `--colors` takes explicit hex color pairs (e.g. `--colors "#2CD2B4,#DC1E5A"`), is repeatable, and produces one variation per pair.
- `requirements-dev.txt` declaring pytest, so the test suite can be installed and run from a clean checkout.

### Changed

- The processing pipeline no longer depends on tkinter: errors are raised as exceptions instead of being reported in message boxes, and the module can be imported on systems without a display or tkinter installed. The GUI (`select_image`) is now a thin wrapper around the pipeline, preserving the previous dialog behavior.
- Added type hints throughout `duotone_generator.py` (evaluated lazily via `from __future__ import annotations`), extracted `DEFAULT_VARIATION_COUNT`, and normalized the `create_duotone_image` docstring to Google style, now documenting its BGR return value. No behavior changes.

### Fixed

- Removed GIF from the supported formats in the file dialog, the `convert_to_duotone` docstring, and the CLI help: `cv2.imread` cannot decode GIF, so the advertised support always failed.
- `convert_to_duotone` now raises `IOError` when `cv2.imwrite` fails (for example, an unwritable output directory) instead of reporting success.
- `hex_to_rgb` no longer accepts strings with more than one leading `#`.
- Running with no arguments on a system without tkinter now exits with a clear message instead of a raw `ImportError` traceback.

## [1.1.1] - 2026-05-03

### Added

- `convert_to_duotone` now accepts an optional `output_dir` argument so the output folder is always placed in a known location, independent of where the source file lives. Omitting the argument preserves the original sibling-of-source behavior.
- The GUI (`select_image`) now opens a second dialog prompting the user to choose an output directory. Cancelling either dialog aborts cleanly with no side effects.

## [1.1.0] - 2026-04-29

### Added

- Output images are now saved as lossless **PNG** files, preserving full color fidelity for use in design tools.
- Filenames now use **human-readable hex color codes** in RGB order (e.g. `083_2CD2B4_DC1E5A.png`), making it straightforward to copy a value directly into Figma, Illustrator, or a style guide.
- A **`colors.csv` sidecar file** is written alongside each batch. It lists every variation's index and both hex codes, enabling designers to reference or share the full palette without opening individual files.

### Fixed

- Corrected a channel-order bug where the red and blue channels in output images were swapped (OpenCV's BGR convention was not applied after the RGB blend), meaning saved colors did not match the intended values.

### Changed

- Output filenames no longer include raw BGR integer tuples or the redundant `_duotone_` and `_variation` labels.
- `csv` (Python standard library) added to imports; no new third-party dependencies.

## [1.0.0] - 2024-08-20

### Added

- Initial release: file-dialog image selection, 100 random duotone variations exported as JPEG, output saved to a sibling folder.
