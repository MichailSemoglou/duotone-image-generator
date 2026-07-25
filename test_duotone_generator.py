"""
Tests for duotone_generator.py

Run with:
    pytest test_duotone_generator.py
"""

import csv
import os
import random
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

import duotone_generator as dg

SCRIPT = Path(__file__).resolve().parent / "duotone_generator.py"


# ---------------------------------------------------------------------------
# rgb_to_hex
# ---------------------------------------------------------------------------

class TestRgbToHex:
    def test_black(self):
        assert dg.rgb_to_hex([0, 0, 0]) == "#000000"

    def test_white(self):
        assert dg.rgb_to_hex([255, 255, 255]) == "#FFFFFF"

    def test_known_color(self):
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
# hex_to_rgb
# ---------------------------------------------------------------------------

class TestHexToRgb:
    def test_with_hash(self):
        assert dg.hex_to_rgb("#2CD2B4") == [44, 210, 180]

    def test_without_hash(self):
        assert dg.hex_to_rgb("2CD2B4") == [44, 210, 180]

    def test_lowercase(self):
        assert dg.hex_to_rgb("#2cd2b4") == [44, 210, 180]

    def test_round_trip(self):
        assert dg.hex_to_rgb(dg.rgb_to_hex([1, 2, 3])) == [1, 2, 3]

    def test_wrong_length_raises(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            dg.hex_to_rgb("#FFF")

    def test_invalid_characters_raise(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            dg.hex_to_rgb("#GGGGGG")

    def test_multiple_hash_prefixes_raise(self):
        # lstrip-style over-acceptance: only one leading '#' is allowed.
        with pytest.raises(ValueError, match="Invalid hex color"):
            dg.hex_to_rgb("##FF0000")


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

    def test_seeded_rng_instances_match(self):
        rng_a = random.Random(1)
        rng_b = random.Random(1)
        assert dg.generate_random_color(rng_a) == dg.generate_random_color(rng_b)


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
        # A pure-red RGB color (255,0,0) should appear as (0,0,255) in BGR.
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

    def test_midtones_round_to_nearest_uint8(self):
        # 0.5 * 255 = 127.5 must round to 128, not truncate to 127. Every
        # intermediate here is exact in float32, so exact equality holds.
        gray = self._flat_gray(0.5)
        result = dg.create_duotone_image(gray, [0, 0, 0], [255, 255, 255])
        assert result[0, 0].tolist() == [128, 128, 128]


# ---------------------------------------------------------------------------
# convert_to_duotone  (integration — writes real files to a temp dir)
# ---------------------------------------------------------------------------

class TestConvertToDuotone:
    """End-to-end tests that write to a temporary directory."""

    @pytest.fixture
    def source_image(self, tmp_path):
        """Write a small solid-color PNG and return its path."""
        img = np.zeros((16, 16, 3), dtype=np.uint8)
        img[:] = [128, 64, 192]
        path = str(tmp_path / "source.png")
        cv2.imwrite(path, img)
        return path

    def _run(self, source_image):
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

    def test_returns_output_folder_and_color_records(self, source_image, tmp_path):
        output_folder, records = dg.convert_to_duotone(source_image)
        assert output_folder == str(tmp_path / "source_duotone_variations")
        assert len(records) == 100
        assert all(len(record) == 3 for record in records)

    def test_custom_output_dir(self, source_image, tmp_path):
        out_dir = tmp_path / "custom_out"
        out_dir.mkdir()
        output_folder, _ = dg.convert_to_duotone(source_image, output_dir=str(out_dir))
        assert output_folder == str(out_dir / "source_duotone_variations")
        assert (out_dir / "source_duotone_variations").is_dir()

    def test_invalid_path_raises(self, tmp_path):
        # The pipeline raises instead of reporting via a messagebox.
        with pytest.raises(ValueError, match="Failed to load image"):
            dg.convert_to_duotone(str(tmp_path / "nonexistent.png"))

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="chmod-based read-only directories do not block writes on Windows",
    )
    @pytest.mark.skipif(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        reason="root bypasses permission bits on read-only directories",
    )
    def test_unwritable_output_raises(self, source_image, tmp_path):
        # cv2.imwrite returns False when it cannot write; that must surface.
        folder = tmp_path / "out" / "source_duotone_variations"
        folder.mkdir(parents=True)
        folder.chmod(0o555)
        try:
            with pytest.raises(IOError, match="Failed to write"):
                dg.convert_to_duotone(source_image, output_dir=str(tmp_path / "out"))
        finally:
            folder.chmod(0o755)

    # -- input hardening ----------------------------------------------------

    def test_unsupported_extension_raises(self, source_image, tmp_path):
        # Valid PNG content under a .gif name must still be rejected: the
        # extension is checked before any decoding happens.
        renamed = tmp_path / "renamed.gif"
        renamed.write_bytes(Path(source_image).read_bytes())
        with pytest.raises(ValueError, match="Unsupported image format"):
            dg.convert_to_duotone(str(renamed))

    def test_missing_extension_raises(self, source_image, tmp_path):
        renamed = tmp_path / "source"
        renamed.write_bytes(Path(source_image).read_bytes())
        with pytest.raises(ValueError, match="Unsupported image format"):
            dg.convert_to_duotone(str(renamed))

    def test_uppercase_extension_accepted(self, source_image, tmp_path):
        upper = tmp_path / "UPPER.PNG"
        upper.write_bytes(Path(source_image).read_bytes())
        _, records = dg.convert_to_duotone(str(upper), count=1)
        assert len(records) == 1

    def test_zero_byte_file_raises(self, tmp_path):
        empty = tmp_path / "empty.png"
        empty.touch()
        with pytest.raises(ValueError, match="file is empty"):
            dg.convert_to_duotone(str(empty))

    def test_oversized_image_raises(self, source_image, monkeypatch):
        # A 16x16 source with the limit patched down to 8 exercises the guard
        # without allocating a real gigapixel image.
        monkeypatch.setattr(dg, "MAX_IMAGE_DIMENSION", 8)
        with pytest.raises(ValueError, match="maximum supported dimension"):
            dg.convert_to_duotone(source_image)

    def test_image_at_exact_dimension_limit_accepted(self, source_image, monkeypatch):
        monkeypatch.setattr(dg, "MAX_IMAGE_DIMENSION", 16)
        _, records = dg.convert_to_duotone(source_image, count=1)
        assert len(records) == 1

    # -- count ------------------------------------------------------------

    def test_count_limits_number_of_variations(self, source_image, tmp_path):
        _, records = dg.convert_to_duotone(source_image, count=5)
        folder = tmp_path / "source_duotone_variations"
        assert len(records) == 5
        assert len(list(folder.glob("*.png"))) == 5

    def test_count_must_be_positive(self, source_image):
        with pytest.raises(ValueError, match="count must be at least 1"):
            dg.convert_to_duotone(source_image, count=0)

    # -- seed -------------------------------------------------------------

    def test_seed_produces_identical_batches(self, source_image, tmp_path):
        _, records_a = dg.convert_to_duotone(source_image, output_dir=str(tmp_path / "a"), seed=42)
        _, records_b = dg.convert_to_duotone(source_image, output_dir=str(tmp_path / "b"), seed=42)
        assert records_a == records_b

    def test_seed_matches_known_sequence(self, source_image, tmp_path):
        # random.Random(42) deterministically yields this exact first pair.
        _, records = dg.convert_to_duotone(source_image, seed=42)
        assert records[0] == [0, "#390C8C", "#7D7247"]
        folder = tmp_path / "source_duotone_variations"
        assert (folder / "000_390C8C_7D7247.png").is_file()

    # -- explicit colors -------------------------------------------------

    def test_explicit_colors_produce_single_variation(self, source_image, tmp_path):
        _, records = dg.convert_to_duotone(
            source_image, colors=[([44, 210, 180], [220, 30, 90])]
        )
        assert records == [[0, "#2CD2B4", "#DC1E5A"]]
        folder = tmp_path / "source_duotone_variations"
        assert (folder / "000_2CD2B4_DC1E5A.png").is_file()

    def test_explicit_colors_one_variation_per_pair(self, source_image, tmp_path):
        pairs = [([255, 0, 0], [0, 0, 255]), ([0, 0, 0], [255, 255, 255])]
        _, records = dg.convert_to_duotone(source_image, colors=pairs)
        assert records == [[0, "#FF0000", "#0000FF"], [1, "#000000", "#FFFFFF"]]

    def test_empty_colors_raises(self, source_image):
        with pytest.raises(ValueError, match="at least one"):
            dg.convert_to_duotone(source_image, colors=[])

    def test_colors_out_of_range_raises(self, source_image):
        with pytest.raises(ValueError, match="Invalid RGB color"):
            dg.convert_to_duotone(source_image, colors=[([300, 0, 0], [0, 0, 0])])

    def test_colors_negative_value_raises(self, source_image):
        with pytest.raises(ValueError, match="Invalid RGB color"):
            dg.convert_to_duotone(source_image, colors=[([-1, 0, 0], [0, 0, 0])])

    def test_colors_wrong_length_raises(self, source_image):
        with pytest.raises(ValueError, match="Invalid RGB color"):
            dg.convert_to_duotone(source_image, colors=[([255, 0], [0, 0, 0])])

    def test_duplicate_color_pairs_raise_before_writing(self, source_image, tmp_path):
        # Identical pairs map to identical filenames, so the second write
        # would silently overwrite the first. Validation must fire before
        # any output is created.
        pairs = [([255, 0, 0], [0, 0, 255]), ([255, 0, 0], [0, 0, 255])]
        with pytest.raises(ValueError, match="Duplicate color pair"):
            dg.convert_to_duotone(source_image, colors=pairs)
        assert not (tmp_path / "source_duotone_variations").exists()


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for the command-line entry point."""

    @pytest.fixture
    def source_image(self, tmp_path):
        """Write a small solid-color PNG and return its path."""
        img = np.zeros((16, 16, 3), dtype=np.uint8)
        img[:] = [128, 64, 192]
        path = str(tmp_path / "source.png")
        cv2.imwrite(path, img)
        return path

    def test_cli_generates_variations(self, source_image, tmp_path, capsys):
        dg.main([source_image])
        assert (tmp_path / "source_duotone_variations").is_dir()
        assert "generated successfully" in capsys.readouterr().out

    def test_cli_output_dir_option(self, source_image, tmp_path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        dg.main([source_image, "--output-dir", str(out_dir)])
        assert (out_dir / "source_duotone_variations").is_dir()

    def test_cli_invalid_path_exits_nonzero(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            dg.main([str(tmp_path / "nonexistent.png")])
        assert exc_info.value.code == 1

    def test_no_arguments_launches_gui(self, monkeypatch):
        calls = []
        monkeypatch.setattr(dg, "select_image", lambda: calls.append(True))
        dg.main([])
        assert calls == [True]

    def test_no_arguments_without_tkinter_exits_cleanly(self, monkeypatch):
        def raise_import_error():
            raise ImportError("No module named 'tkinter'")

        monkeypatch.setattr(dg, "select_image", raise_import_error)
        with pytest.raises(SystemExit) as exc_info:
            dg.main([])
        assert exc_info.value.code == 1

    def test_cli_count_option(self, source_image, tmp_path):
        dg.main([source_image, "--count", "3"])
        folder = tmp_path / "source_duotone_variations"
        assert len(list(folder.glob("*.png"))) == 3

    def test_cli_seed_is_reproducible(self, source_image, tmp_path):
        dg.main([source_image, "-o", str(tmp_path / "a"), "--seed", "7"])
        dg.main([source_image, "-o", str(tmp_path / "b"), "--seed", "7"])
        names_a = sorted(p.name for p in (tmp_path / "a" / "source_duotone_variations").glob("*.png"))
        names_b = sorted(p.name for p in (tmp_path / "b" / "source_duotone_variations").glob("*.png"))
        assert names_a == names_b
        assert len(names_a) == 100

    def test_cli_colors_generates_single_variation(self, source_image, tmp_path):
        dg.main([source_image, "--colors", "#2CD2B4,#DC1E5A"])
        folder = tmp_path / "source_duotone_variations"
        assert [p.name for p in folder.glob("*.png")] == ["000_2CD2B4_DC1E5A.png"]

    def test_cli_colors_conflicts_with_count_and_seed(self, source_image):
        for extra in (["--count", "5"], ["--seed", "1"]):
            with pytest.raises(SystemExit) as exc_info:
                dg.main([source_image, "--colors", "#2CD2B4,#DC1E5A"] + extra)
            assert exc_info.value.code == 2

    def test_cli_invalid_hex_exits_with_usage_error(self, source_image):
        with pytest.raises(SystemExit) as exc_info:
            dg.main([source_image, "--colors", "notahex"])
        assert exc_info.value.code == 2

    def test_cli_flags_without_image_are_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            dg.main(["--count", "5"])
        assert exc_info.value.code == 2

    def test_script_entry_point_generates_variations(self, source_image, tmp_path):
        # Exercises `if __name__ == "__main__"`, which the import-based
        # tests above never reach.
        result = subprocess.run(
            [sys.executable, str(SCRIPT), source_image, "--count", "2"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "2 duotone variations" in result.stdout
        folder = tmp_path / "source_duotone_variations"
        assert len(list(folder.glob("*.png"))) == 2


# ---------------------------------------------------------------------------
# headless import
# ---------------------------------------------------------------------------

class TestHeadlessImport:
    def test_module_imports_without_tkinter(self):
        # tkinter is imported lazily inside select_image, so the module must
        # import on systems where tkinter is not installed at all. Mapping
        # the name to None in sys.modules makes any 'import tkinter' raise
        # ImportError in the child process.
        code = (
            "import sys; sys.modules['tkinter'] = None; "
            "import duotone_generator"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True,
            cwd=SCRIPT.parent,
        )
        assert result.returncode == 0, result.stderr
