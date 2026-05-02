import csv
import cv2
import numpy as np
import random
import os
from tkinter import filedialog, messagebox

def select_image():
    """Open file dialogs to select a source image and an output directory, then process."""
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
    if not image_path:
        return
    output_dir = filedialog.askdirectory(title="Select output directory")
    if not output_dir:
        return
    convert_to_duotone(image_path, output_dir=output_dir)

def generate_random_color():
    """Generate a random RGB color."""
    return [random.randint(0, 255) for _ in range(3)]

def rgb_to_hex(color):
    """Convert an RGB list to a hex string."""
    return "#{:02X}{:02X}{:02X}".format(color[0], color[1], color[2])

def create_duotone_image(gray, color1, color2):
    """
    Create a duotone image from a grayscale image and two colors.
    
    Args:
    gray (np.array): Grayscale image normalized to [0, 1]
    color1 (list): First RGB color
    color2 (list): Second RGB color
    
    Returns:
    np.array: Duotone image
    """
    color1 = np.array(color1, dtype=np.float32).reshape(1, 1, 3) / 255
    color2 = np.array(color2, dtype=np.float32).reshape(1, 1, 3) / 255
    
    duotone = (1 - gray)[:, :, np.newaxis] * color1 + gray[:, :, np.newaxis] * color2
    duotone_rgb = np.clip(duotone * 255, 0, 255).astype(np.uint8)
    return cv2.cvtColor(duotone_rgb, cv2.COLOR_RGB2BGR)

def convert_to_duotone(image_path, output_dir=None):
    """
    Convert an image to 100 duotone variations and save them to disk.

    For each variation a random RGB colour pair is generated, blended over the
    grayscale source, and written as a lossless PNG. Filenames encode both hex
    colour values (e.g. '083_#2CD2B4_#DC1E5A.png'). A 'colors.csv' sidecar is
    also written to the output folder listing every variation's colour pair.

    Args:
        image_path (str): Absolute or relative path to the source image.
            Supported formats: JPEG, PNG, BMP, GIF.
        output_dir (str | None): Directory under which the
            '<image_stem>_duotone_variations' folder is created.  When None
            (default) the folder is placed alongside the source image.

    Side effects:
        Creates '<output_dir>/<image_stem>_duotone_variations/' (or a sibling
        folder when output_dir is None) containing 100 PNG files and one
        'colors.csv' file.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image '{image_path}'.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255

        stem = os.path.splitext(os.path.basename(image_path))[0]
        base = output_dir if output_dir is not None else os.path.dirname(image_path)
        output_folder = os.path.join(base, f"{stem}_duotone_variations")
        os.makedirs(output_folder, exist_ok=True)

        color_records = []
        for i in range(100):
            color1, color2 = generate_random_color(), generate_random_color()
            duotone = create_duotone_image(gray, color1, color2)

            hex1 = rgb_to_hex(color1)
            hex2 = rgb_to_hex(color2)

            filename = f"{i:03d}_{hex1.lstrip('#')}_{hex2.lstrip('#')}.png"
            output_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_path, duotone)
            color_records.append([i, hex1, hex2])

        csv_path = os.path.join(output_folder, "colors.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["variation", "color_1_hex", "color_2_hex"])
            writer.writerows(color_records)

        messagebox.showinfo("Success", f"100 duotone variations generated successfully in '{output_folder}'.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    select_image()