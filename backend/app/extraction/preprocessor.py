import os
import math
import uuid
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False
from PIL import Image

from typing import Any

def preprocess_image(image_path: str) -> Any:
    """Preprocess image for OCR. Returns numpy array if cv2 available, else PIL Image."""
    if not CV2_AVAILABLE:
        # Fallback: return PIL image for VLM path
        img = Image.open(image_path)
        img.load() # Force load to release file lock on Windows
        return img

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")
        
    h, w = image.shape[:2]
    
    # Upscale if width < 1500px
    if w < 1500:
        scale_factor = 1500 / w
        image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Deskew
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    if abs(angle) > 0.5:
        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Bilateral filter denoising
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    
    # Adaptive Gaussian thresholding
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 11
    )
    
    # Morphological close
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return cleaned

def pdf_to_images(
    pdf_path: str,
    max_pages: int = 30,
    max_page_pixels: int = 40_000_000,
    max_total_pixels: int = 40_000_000,
) -> list[str]:
    """Convert PDF pages to temporary image files."""
    import fitz
    doc = fitz.open(pdf_path)
    if len(doc) == 0 or len(doc) > max_pages:
        doc.close()
        raise ValueError(f"PDF page count must be between 1 and {max_pages}")
    image_paths = []
    
    temp_dir = os.path.dirname(pdf_path)
    try:
        pages = list(doc)
        page_sizes = []
        total_pixels = 0
        for page in pages:
            width = math.ceil(page.rect.width * 150 / 72)
            height = math.ceil(page.rect.height * 150 / 72)
            page_pixels = width * height
            if page_pixels <= 0 or page_pixels > max_page_pixels:
                raise ValueError("PDF page dimensions exceed the processing limit")
            total_pixels += page_pixels
            if total_pixels > max_total_pixels:
                raise ValueError("PDF total pixel count exceeds the processing limit")
            page_sizes.append(page_pixels)

        for i, page in enumerate(pages):
            pix = page.get_pixmap(dpi=150)
            path = os.path.join(temp_dir, f"temp_page_{uuid.uuid4().hex}_{i}.png")
            pix.save(path)
            image_paths.append(path)
    except Exception:
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        doc.close()
        raise
    doc.close()
    return image_paths

def prepare_document(
    file_path: str,
    max_pages: int = 30,
    max_total_pixels: int = 40_000_000,
) -> list[Any]:
    """Dispatcher to prepare a document (PDF or Image)."""
    ext = file_path.lower().split('.')[-1]
    
    if ext == 'pdf':
        image_paths = pdf_to_images(file_path, max_pages=max_pages, max_total_pixels=max_total_pixels)
        try:
            return [preprocess_image(path) for path in image_paths]
        finally:
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
    else:
        with Image.open(file_path) as image:
            if image.width * image.height > max_total_pixels:
                raise ValueError("Image dimensions exceed the processing limit")
        return [preprocess_image(file_path)]

