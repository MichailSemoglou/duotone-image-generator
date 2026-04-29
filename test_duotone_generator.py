"""
Tests for duotone_generator.py

Run with:
    pytest test_duotone_generator.py
"""

import csv
import os
import tempfile
from unittest.mock import patch

import cv2
import numpy as np
import pytest

# Suppress any tkinter display attempts during import on headless systems.
import tkinter.filedialog
import tkinter.messagebox
with patch("tkinter.filedialog.askopenfilename", return_value=""), \
     patch("tkinter.messagebox.showinfo"), \
     patch("tkinter.messagebox.showerror"):
    import duotone_generator as dg


# ---------------------------------------------------------------------------
# rgb_to_hex
# ---------------------------------------------------------------------------

class TestRgbToHex:
    def test_black(self):
        assert dg.rgb_to_hex([0, 0, 0]) == "#000000"

    def test_white(self):
        assert dg.rgb_to_hex([255, 255, 255]) == "#FFFFFF"

    def test_known_colour(self):
        assert dg.rgb_to_hex([44, 210, 180]) == "#2CD2B4"

    def test_uppercase(self):
        # Hex digits must be uppercase so they paste correctly into design tools.
        result = dg.rgb_to_hex([171, 205, 239])
        assert result == result.upper()

    def test_format_starts_with_hash(self):
        assert dg.rgb_to_hex([10, 20, 30]).startswith("#")

    def test_length(self):
        assert len(dg.rgb_to_hex([10, 20, 30])) == 7


# ---------------------------------------------------------------------------
# generate_random_color
# ---------------------------------------------------------------------------

class TestGenerateRandomColor:
    def test_returns_list_of_three(self):
        color = dg.generate_random_color()
        assert isinstance(color, list)
        assert len(color) == 3

    def test_values_in_range(self):
        for _ in range(50):
            color = dg.generate_random_color()
            assert all(0 <= v <= 255 for v in color)

    def test_values_are_integers(self):
        color = dg.generate_random_color()
        assert all(isinstance(v, int) for v in color)

    def test_produces_different_colors(self):
        # Astronomically unlikely to collide 20 times in a row.
        colors = [tuple(dg.generate_random_color()) for _ in range(20)]
        assert len(set(colors)) > 1


# ---------------------------------------------------------------------------
# create_duotone_image
# ---------------------------------------------------------------------------

class TestCreateDuotoneImage:
    """Tests for the core blend function."""

    def _flat_gray(self, value, h=4, w=4):
        """Return an HxW float32 grayscale array filled with `value`."""
        return np.full((h, w), value, dtype=np.float32)

    def test_output_shape_matches_input(self):
        gray = self._flat_gray(0.5, h=8, w=6)
        result = dg.create_duotone_image(gray, [255, 0, 0], [0, 0, 255])
        assert result.shape == (8, 6, 3)

    def test_output_dtype_is_uint8(self):
        gray = self._flat_gray(0.5)
        result = dg.create_duotone_image(gray, [100, 150, 200], [50, 60, 70])
        assert result.dtype == np.uint8

    def test_pure_black_source_maps_to_color1(self):
        # gray = 0 everywhere → blend = 1*color1 + 0*color2 = color1 (in BGR)
        gray = self._flat_gray(0.0)
        color1_rgb = [200, 100, 50]
        color2_rgb = [10, 20, 30]
        result = dg.create_duotone_image(gray, color1_rgb, color2_rgb)
        expected_bgr = [color1_rgb[2], color1_rgb[1], color1_rgb[0]]
        pixel = result[0, 0].tolist()
        assert pixel == pytest.approx(expected_bgr, abs=1)

    def test_pure_white_source_maps_to_color2(self):
        # gray = 1 everywhere → blend = 0*color1 + 1*color2 = color2 (in BGR)
        gray = self._flat_gray(1.0)
        color1_rgb = [200, 100, 50]
        color2_rgb = [10, 20, 30]
        result = dg.create_duotone_image(gray, color1_rgb, color2_rgb)
        expected_bgr = [color2_rgb[2], color2_rgb[1], color2_rgb[0]]
        pixel = result[0, 0].tolist()
        assert pixel == pytest.approx(expected_bgr, abs=1)

    def test_output_is_bgr_not_rgb(self):
        # A pure-red RGB colour (255,0,0) should appear as (0,0,255) in BGR.
        gray = self._flat_gray(0.0)
        result = dg.create_duotone_image(gray, [255, 0, 0], [0, 0, 0])
        b, _, r = result[0, 0]
        assert r == pytest.approx(255, abs=1)
        assert b == pytest.approx(0, abs=1)

    def test_pixel_values_clipped_to_uint8_range(self):
        gray = self._flat_gray(0.5)
        result = dg.create_duotone_image(gray, [255, 255, 255], [255, 255, 255])
        assert result.max() <= 255
        assert result.min() >= 0


# ---------------------------------------------------------------------------
# convert_to_duotone  (integration — writes real files to a temp dir)
# ---------------------------------------------------------------------------

class TestConvertToDuotone:
    """End-to-end tests that write to a temporary directory."""

    @pytest.fixture
    def source_image(self, tmp_path):
        """Write a small solid-colour PNG and return its path."""
        img = np.zeros((16, 16, 3), dtype=np.uint8)
        img[:] = [128, 64, 192]
        path = str(tmp_path / "source.png")
        cv2.imwrite(path, img)
        return path

    def _run(self, source_image):
        with patch("tkinter.messagebox.showinfo"), \
             patch("tkinter.messagebox.showerror"):
            dg.convert_to_duotone(source_image)

    def test_output_folder_created(self, source_image, tmp_path):
        self._run(source_image)
        expected = tmp_path / "source_duotone_variations"
        assert expected.is_dir()

    def test_exactly_100_png_files_created(self, source_image, tmp_path):
        self._run(source_image)
        folder = tmp_path / "source_duotone_variations"
        pngs = list(folder.glob("*.png"))
        assert len(pngs) == 100

    def test_filenames_use_hex_notation(self, source_image, tmp_path):
        self._run(source_image)
        folder = tmp_path / "source_duotone_variations"
        for png in folder.glob("*.png"):
            # Expect pattern: NNN_RRGGBB_RRGGBB.png (no leading #)
            parts = png.stem.split("_")
            assert len(parts) == 3, f"Unexpected filename: {png.name}"
            assert len(parts[1]) == 6 and all(c in "0123456789ABCDEFabcdef" for c in parts[1])
            assert len(parts[2]) == 6 and all(c in "0123456789ABCDEFabcdef" for c in parts[2])

    def test_no_jpeg_files_produced(self, source_image, tmp_path):
        self._run(source_image)
        folder = tmp_path / "source_duotone_variations"
        jpegs = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg"))
        assert jpegs == []

    def test_colors_csv_exists(self, source_image, tmp_path):
        self._run(source_image)
        csv_path = tmp_path / "source_duotone_variations" / "colors.csv"
        assert csv_path.is_file()

    def test_colors_csv_has_correct_structure(self, source_image, tmp_path):
        self._run(source_image)
        csv_path = tmp_path / "source_duotone_variations" / "colors.csv"
        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["variation", "color_1_hex", "color_2_hex"]
        assert len(rows) == 101  # header + 100 data rows

    def test_colors_csv_hex_values_match_filenames(self, source_image, tmp_path):
        self._run(source_image)
        folder = tmp_path / "source_duotone_variations"
        csv_path = folder / "colors.csv"
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                idx = int(row["variation"])
                expected_name = f"{idx:03d}_{row['color_1_hex'].lstrip('#')}_{row['color_2_hex'].lstrip('#')}.png"
                assert (folder / expected_name).exists(), \
                    f"File {expected_name} not found"

    def test_invalid_path_does_not_raise(self, tmp_path):
        # messagebox.showerror should be called, not an uncaught exception.
        with patch("tkinter.messagebox.showerror") as mock_err, \
             patch("tkinter.messagebox.showinfo"):
            dg.convert_to_duotone(str(tmp_path / "nonexistent.png"))
        mock_err.assert_called_once()
