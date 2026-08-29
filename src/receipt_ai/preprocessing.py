# -*- coding: utf-8 -*-
"""Image preprocessing pipeline for receipt images."""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .schemas import FieldStatus, ExtractedField
from .quality import assess_image_quality, get_preprocessing_recommendations


def resize_image(image: np.ndarray, max_dim: int = 2000) -> np.ndarray:
    """Resize image if it exceeds max dimension while maintaining aspect ratio."""
    height, width = image.shape[:2]

    if max(width, height) <= max_dim:
        return image

    if width > height:
        new_width = max_dim
        new_height = int(height * (max_dim / width))
    else:
        new_height = max_dim
        new_width = int(width * (max_dim / height))

    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    return resized


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale."""
    if len(image.shape) == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Convert back to BGR if original was color
    if len(image.shape) == 3 and image.shape[2] == 3:
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    return enhanced


def denoise_image(image: np.ndarray) -> np.ndarray:
    """Reduce noise using Gaussian blur (OpenCV compatible alternative)."""
    if len(image.shape) == 3:
        # Use Gaussian blur as a compatible alternative to fastNlDenoiseColored
        return cv2.GaussianBlur(image, (5, 5), 0)
    else:
        return cv2.GaussianBlur(image, (5, 5), 0)


def apply_adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Apply adaptive thresholding for binarization."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    thresholded = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return thresholded


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Deskew image using Hough Transform."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Threshold to binary
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Find coordinates of non-zero pixels
    coords = np.column_stack(np.where(binary > 0))

    if len(coords) == 0:
        return image

    # Fit minimum area rectangle
    angle = cv2.minAreaRect(coords)[-1]

    # OpenCV returns angle in [-90, 0), adjust to [0, 90)
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        gray, rotation_matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )

    return rotated


def preprocess_image(
    image: np.ndarray,
    quality: Optional[Dict[str, Any]] = None,
    variants: Optional[List[int]] = None,
) -> List[np.ndarray]:
    """Create preprocessing variants for a receipt image.

    For difficult images, multiple preprocessing paths may be used.
    The number of variants depends on image quality.

    Variants:
    0: Original
    1: Grayscale
    2: Contrast enhanced
    3: Denoised + enhanced
    4: Thresholded
    5: Deskewed
    """
    if quality is None:
        quality = assess_image_quality(image)

    recs = get_preprocessing_recommendations(quality)

    # Always create at least the original
    variants_list = [image.copy()]

    # Build variants based on recommendations
    processed = image.copy()

    # Variant 1: Grayscale
    if "denoise" in recs or "minimal" in recs:
        processed = denoise_image(processed)
    processed_gray = to_grayscale(processed)
    variants_list.append(cv2.cvtColor(processed_gray, cv2.COLOR_GRAY2BGR) if len(image.shape) == 3 else processed_gray)

    # Variant 2: Contrast enhanced
    processed2 = enhance_contrast(image.copy())
    variants_list.append(processed2)

    # Variant 3: Denoised + enhanced
    processed3 = denoise_image(image.copy())
    processed3 = enhance_contrast(processed3)
    variants_list.append(processed3)

    # Variant 4: Thresholded
    processed4 = apply_adaptive_threshold(image)
    variants_list.append(cv2.cvtColor(processed4, cv2.COLOR_GRAY2BGR) if len(image.shape) == 3 else processed4)

    # Variant 5: Deskewed
    processed5 = deskew_image(image.copy())
    variants_list.append(cv2.cvtColor(processed5, cv2.COLOR_GRAY2BGR) if len(image.shape) == 3 and processed5.dtype != image.dtype else processed5)

    # If original is already grayscale, reduce variants
    if len(image.shape) == 2:
        variants_list = [v if len(v.shape) == 2 else cv2.cvtColor(v, cv2.COLOR_GRAY2BGR) for v in variants_list[:3]]

    return variants_list


def preprocess_image_path(
    image_path: Path,
    output_dir: Optional[Path] = None,
    variants: Optional[List[int]] = None,
) -> List[Tuple[np.ndarray, str]]:
    """Load image from path and create preprocessing variants.

    Returns list of (image_variant, variant_name) tuples.
    """
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    quality = assess_image_quality(image)
    variant_images = preprocess_image(image, quality, variants)

    variant_names = []
    for i, var in enumerate(variant_images):
        if variants is not None and i < len(variants):
            idx = variants[i]
            if idx == 0:
                name = "original"
            elif idx == 1:
                name = "grayscale"
            elif idx == 2:
                name = "contrast_enhanced"
            elif idx == 3:
                name = "denoised_enhanced"
            elif idx == 4:
                name = "thresholded"
            elif idx == 5:
                name = "deskewed"
            else:
                name = f"variant_{idx}"
        else:
            name = f"variant_{i}"
        variant_names.append((var, name))

    return variant_images, quality, variant_names


# Export all functions
__all__ = [
    "resize_image",
    "to_grayscale",
    "enhance_contrast",
    "denoise_image",
    "apply_adaptive_threshold",
    "deskew_image",
    "preprocess_image",
    "preprocess_image_path",
]