"""Duotone image generator: pure processing pipeline with GUI and CLI shells."""

from __future__ import annotations

import argparse
import csv
import os
import random

import cv2
import numpy as np

DEFAULT_VARIATION_COUNT = 100


def _success_message(output_folder: str, count: int) -> str:
    """Build the completion message shared by the GUI and CLI shells."""
    noun = "variation" if count == 1 else "variations"
    return f"{count} duotone {noun} generated successfully in '{output_folder}'."


def select_image() -> None:
    """Open file dialogs to select a source image and output directory, then process."""
    from tkinter import filedialog, messagebox

    image_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
    )
    if not image_path:
        return
    output_dir = filedialog.askdirectory(title="Select output directory")
    if not output_dir:
        return
    try:
        output_folder, records = convert_to_duotone(image_path, output_dir=output_dir)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        return
    messagebox.showinfo("Success", _success_message(output_folder, len(records)))


def generate_random_color(rng: random.Random | None = None) -> list[int]:
    """Generate a random RGB color, optionally from a seeded Random instance."""
    source = rng if rng is not None else random
    return [source.randint(0, 255) for _ in range(3)]


def rgb_to_hex(color: list[int]) -> str:
    """Convert an RGB list to a hex string."""
    return "#{:02X}{:02X}{:02X}".format(color[0], color[1], color[2])


def hex_to_rgb(value: str) -> list[int]:
    """
    Convert a hex color string to an RGB list.

    Accepts '#RRGGBB' and 'RRGGBB', case-insensitively.
    Raises ValueError for anything else.
    """
    text = value.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6:
        raise ValueError(f"Invalid hex color '{value}': expected '#RRGGBB'.")
    try:
        return [int(text[i:i + 2], 16) for i in (0, 2, 4)]
    except ValueError:
        raise ValueError(f"Invalid hex color '{value}': expected '#RRGGBB'.")


def parse_color_pair(spec: str) -> tuple[list[int], list[int]]:
    """Parse a 'HEX1,HEX2' string into a pair of RGB lists."""
    parts = spec.split(",")
    if len(parts) != 2:
        raise ValueError(f"Invalid color pair '{spec}': expected 'HEX1,HEX2'.")
    return hex_to_rgb(parts[0]), hex_to_rgb(parts[1])


def create_duotone_image(
    gray: np.ndarray,
    color1: list[int],
    color2: list[int],
) -> np.ndarray:
    """
    Create a duotone image from a grayscale image and two colors.

    Args:
        gray: Grayscale image as a float array normalized to [0, 1].
        color1: First RGB color, three integers in [0, 255]. Maps to black.
        color2: Second RGB color, three integers in [0, 255]. Maps to white.

    Returns:
        The duotone image as a uint8 array in OpenCV's BGR channel order,
        ready for cv2.imwrite.
    """
    c1 = np.array(color1, dtype=np.float32).reshape(1, 1, 3) / 255
    c2 = np.array(color2, dtype=np.float32).reshape(1, 1, 3) / 255

    duotone = (1 - gray)[:, :, np.newaxis] * c1 + gray[:, :, np.newaxis] * c2
    duotone_rgb = np.clip(duotone * 255, 0, 255).astype(np.uint8)
    return cv2.cvtColor(duotone_rgb, cv2.COLOR_RGB2BGR)


def convert_to_duotone(
    image_path: str,
    output_dir: str | None = None,
    count: int = DEFAULT_VARIATION_COUNT,
    seed: int | None = None,
    colors: list[tuple[list[int], list[int]]] | None = None,
) -> tuple[str, list[list[int | str]]]:
    """
    Convert an image to duotone variations and save them to disk.

    For each variation a color pair is blended over the grayscale source and
    written as a lossless PNG. Filenames encode both hex color values
    (e.g. '083_2CD2B4_DC1E5A.png'). A 'colors.csv' sidecar is also written to
    the output folder listing every variation's color pair.

    Args:
        image_path: Absolute or relative path to the source image.
            Supported formats: JPEG, PNG, BMP.
        output_dir: Directory under which the
            '<image_stem>_duotone_variations' folder is created. When None
            (default) the folder is placed alongside the source image.
        count: Number of random variations to generate
            (default: DEFAULT_VARIATION_COUNT). Ignored when `colors` is given.
        seed: Seed for random color generation. Pass an integer to reproduce
            a batch exactly; None (default) produces a different batch
            every run.
        colors: Explicit color pairs as (color1, color2) RGB lists, one
            variation per pair. When given, `count` and `seed` are unused.

    Returns:
        A tuple ``(output_folder, color_records)``: the path of the created
        '<image_stem>_duotone_variations' folder and a list of
        ``[index, color_1_hex, color_2_hex]`` rows, one per variation.

    Raises:
        ValueError: If the source image cannot be loaded, `count` is below 1,
            or `colors` is an empty list.
        IOError: If a variation file cannot be written to disk.

    Side effects:
        Creates '<output_dir>/<image_stem>_duotone_variations/' (or a sibling
        folder when output_dir is None) containing one PNG per variation and
        one 'colors.csv' file.
    """
    if colors is None:
        if count < 1:
            raise ValueError(f"count must be at least 1, got {count}.")
    elif not colors:
        raise ValueError("colors must contain at least one color pair.")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image '{image_path}'.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255

    if colors is None:
        rng = random.Random(seed)
        pairs = [
            (generate_random_color(rng), generate_random_color(rng))
            for _ in range(count)
        ]
    else:
        pairs = list(colors)

    stem = os.path.splitext(os.path.basename(image_path))[0]
    base = output_dir if output_dir is not None else os.path.dirname(image_path)
    output_folder = os.path.join(base, f"{stem}_duotone_variations")
    os.makedirs(output_folder, exist_ok=True)
    for _stale in os.listdir(output_folder):
        if _stale.lower().endswith(".png"):
            os.remove(os.path.join(output_folder, _stale))

    color_records = []
    for i, (color1, color2) in enumerate(pairs):
        duotone = create_duotone_image(gray, color1, color2)

        hex1 = rgb_to_hex(color1)
        hex2 = rgb_to_hex(color2)

        filename = f"{i:03d}_{hex1.lstrip('#')}_{hex2.lstrip('#')}.png"
        output_path = os.path.join(output_folder, filename)
        if not cv2.imwrite(output_path, duotone):
            raise IOError(f"Failed to write '{output_path}'.")
        color_records.append([i, hex1, hex2])

    csv_path = os.path.join(output_folder, "colors.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["variation", "color_1_hex", "color_2_hex"])
        writer.writerows(color_records)

    return output_folder, color_records


def main(argv: list[str] | None = None) -> None:
    """Console entry point: process the image argument, or launch the GUI."""
    parser = argparse.ArgumentParser(
        description="Generate duotone variations of an image."
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Path to the source image (JPEG, PNG, BMP). "
             "When omitted, file dialogs open instead.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Directory under which the output folder is created "
             "(default: alongside the source image).",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=None,
        help=f"Number of random variations to generate "
             f"(default: {DEFAULT_VARIATION_COUNT}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for random color generation; reuse a seed to reproduce "
             "a batch exactly.",
    )
    parser.add_argument(
        "--colors",
        action="append",
        default=None,
        metavar="HEX1,HEX2",
        help="Explicit color pair(s) instead of random ones, e.g. "
             "--colors '#2CD2B4,#DC1E5A'. Repeatable; one variation per pair. "
             "Cannot be combined with --count or --seed.",
    )
    args = parser.parse_args(argv)

    if not args.image:
        if args.count is not None or args.seed is not None or args.colors:
            parser.error("--count, --seed and --colors require an image path")
        try:
            select_image()
        except ImportError:
            parser.exit(1, "Error: tkinter is not installed; "
                           "pass an image path to use CLI mode.\n")
        return

    colors = None
    if args.colors:
        if args.count is not None or args.seed is not None:
            parser.error("--colors cannot be combined with --count or --seed")
        try:
            colors = [parse_color_pair(spec) for spec in args.colors]
        except ValueError as e:
            parser.error(str(e))

    count = args.count if args.count is not None else DEFAULT_VARIATION_COUNT

    try:
        output_folder, records = convert_to_duotone(
            args.image, output_dir=args.output_dir, count=count,
            seed=args.seed, colors=colors,
        )
    except Exception as e:
        parser.exit(1, f"Error: {e}\n")

    print(_success_message(output_folder, len(records)))


if __name__ == "__main__":
    main()
