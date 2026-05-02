# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-05-03

### Added

- `convert_to_duotone` now accepts an optional `output_dir` argument so the output folder is always placed in a known location, independent of where the source file lives. Omitting the argument preserves the original sibling-of-source behaviour.
- The GUI (`select_image`) now opens a second dialog prompting the user to choose an output directory. Cancelling either dialog aborts cleanly with no side effects.

## [1.1.0] - 2026-04-29

### Added

- Output images are now saved as lossless **PNG** files, preserving full colour fidelity for use in design tools.
- Filenames now use **human-readable hex colour codes** in RGB order (e.g. `083_#2CD2B4_#DC1E5A.png`), making it straightforward to copy a value directly into Figma, Illustrator, or a style guide.
- A **`colors.csv` sidecar file** is written alongside each batch. It lists every variation's index and both hex codes, enabling designers to reference or share the full palette without opening individual files.

### Fixed

- Corrected a channel-order bug where the red and blue channels in output images were swapped (OpenCV's BGR convention was not applied after the RGB blend), meaning saved colours did not match the intended values.

### Changed

- Output filenames no longer include raw BGR integer tuples or the redundant `_duotone_` and `_variation` labels.
- `csv` (Python standard library) added to imports; no new third-party dependencies.

## [1.0.0] - 2024-08-20

### Added

- Initial release: file-dialog image selection, 100 random duotone variations exported as JPEG, output saved to a sibling folder.
