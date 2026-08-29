# -*- coding: utf-8 -*-
"""Image quality assessment for receipt images."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from .schemas import FieldStatus, ExtractedField


def assess_blur(image: np.ndarray) -> Tuple[float, str]:
    """Assess image blur using Laplacian variance.

    Returns (score, status) where score is the variance and
    status indicates if the image is blurry.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()

    # Threshold for blurriness - tuned for receipt images
    if variance < 100:
        return float(variance), "BLURRY"
    elif variance < 200:
        return float(variance), "MODERATELY_BLURRY"
    else:
        return float(variance), "SHARP"


def assess_brightness(image: np.ndarray) -> Tuple[float, str]:
    """Assess image brightness using mean pixel value."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)

    if mean_brightness < 50:
        return float(mean_brightness), "DARK"
    elif mean_brightness < 100:
        return float(mean_brightness), "DIM"
    elif mean_brightness > 200:
        return float(mean_brightness), "BRIGHT"
    else:
        return float(mean_brightness), "WELL_LIT"


def assess_contrast(image: np.ndarray) -> Tuple[float, str]:
    """Assess image contrast using standard deviation of pixel values."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    std_dev = np.std(gray)

    if std_dev < 30:
        return float(std_dev), "LOW_CONTRAST"
    elif std_dev < 60:
        return float(std_dev), "MEDIUM_CONTRAST"
    else:
        return float(std_dev), "HIGH_CONTRAST"


def assess_skew(image: np.ndarray) -> Tuple[float, Optional[float]]:
    """Assess image skew using Hough Line Transform.

    Returns (score, angle) where angle is the detected skew in degrees.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    if lines is None:
        return 0.0, None

    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        angles.append(angle)

    if not angles:
        return 0.0, None

    # Median angle as most reliable
    median_angle = np.median(angles)

    # Score based on how many lines agree with the median
    median_count = sum(1 for a in angles if abs(a - median_angle) < 5)
    agreement = median_count / len(angles) if angles else 0

    return float(agreement), float(median_angle)


def assess_image_quality(image: np.ndarray) -> Dict[str, Any]:
    """Comprehensive quality assessment of a receipt image.

    Returns dict with blur, brightness, contrast, skew signals.
    """
    height, width = image.shape[:2]

    blur_score, blur_status = assess_blur(image)
    brightness_score, brightness_status = assess_brightness(image)
    contrast_score, contrast_status = assess_contrast(image)
    skew_agreement, skew_angle = assess_skew(image)

    # Image dimensions check
    dim_aspect_ratio = width / height if height > 0 else 0
    dim_score = min(width, height) / 1000.0  # Normalized size

    quality = {
        "blur_score": round(blur_score, 2),
        "blur_status": blur_status,
        "brightness_score": round(brightness_score, 2),
        "brightness_status": brightness_status,
        "contrast_score": round(contrast_score, 2),
        "contrast_status": contrast_status,
        "skew_agreement": round(skew_agreement, 4),
        "skew_angle": round(skew_angle, 2) if skew_angle else 0.0,
        "width": width,
        "height": height,
        "aspect_ratio": round(dim_aspect_ratio, 2),
        "size_score": round(dim_score, 4),
    }

    return quality


def get_preprocessing_recommendations(quality: Dict[str, Any]) -> List[str]:
    """Get preprocessing recommendations based on quality assessment."""
    recommendations = []

    if quality["blur_status"] in ("BLURRY", "MODERATELY_BLURRY"):
        recommendations.append("denoise")
        recommendations.append("sharpen")

    if quality["brightness_status"] in ("DARK", "DIM"):
        recommendations.append("brighten")
        recommendations.append("contrast_enhance")

    if quality["contrast_status"] in ("LOW_CONTRAST", "MEDIUM_CONTRAST"):
        recommendations.append("clahe")
        recommendations.append("enhance")

    if quality["skew_angle"] and abs(quality["skew_angle"]) > 2:
        recommendations.append("deskew")

    if quality["size_score"] < 0.5:
        recommendations.append("resize")

    if not recommendations:
        recommendations.append("minimal")

    return recommendations


# Export all functions
__all__ = [
    "assess_blur",
    "assess_brightness",
    "assess_contrast",
    "assess_skew",
    "assess_image_quality",
    "get_preprocessing_recommendations",
]