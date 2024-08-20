import cv2
import numpy as np
import random
import os
from tkinter import filedialog, messagebox

def select_image():
    """Open a file dialog to select an image and process it."""
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
    if image_path:
        convert_to_duotone(image_path)

def generate_random_color():
    """Generate a random RGB color."""
    return [random.randint(0, 255) for _ in range(3)]

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
    return np.clip(duotone * 255, 0, 255).astype(np.uint8)

def convert_to_duotone(image_path):
    """
    Convert an image to multiple duotone variations and save them.
    
    Args:
    image_path (str): Path to the input image
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image '{image_path}'.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255

        output_folder = f"{os.path.splitext(image_path)[0]}_duotone_variations"
        os.makedirs(output_folder, exist_ok=True)

        for i in range(100):
            color1, color2 = generate_random_color(), generate_random_color()
            duotone = create_duotone_image(gray, color1, color2)

            color1_str = '_'.join(map(str, color1))
            color2_str = '_'.join(map(str, color2))

            filename = f"{i:03d}_duotone_BGR_{color1_str}_and_{color2_str}_variation.jpg"
            output_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_path, duotone)

        messagebox.showinfo("Success", f"100 duotone variations generated successfully in '{output_folder}'.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    select_image()