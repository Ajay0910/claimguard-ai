import sys
from PIL import Image
import glob
import os

png_files = glob.glob("*.png")
for png in png_files:
    jpg_name = png.replace(".png", ".jpg")
    try:
        im = Image.open(png)
        rgb_im = im.convert('RGB')
        rgb_im.save(jpg_name)
        print(f"Converted {png} to {jpg_name}")
        os.remove(png)
    except Exception as e:
        print(f"Failed to convert {png}: {e}")
