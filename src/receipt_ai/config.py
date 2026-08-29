# -*- coding: utf-8 -*-
"""Configuration for Carbon Crunch Receipt Intelligence."""

import os
from pathlib import Path
from typing import Dict, Any

# Project root directory
_PROJECT_ROOT_HARD = Path("C:/Users/ketan_hvrftcf/OneDrive/Desktop/PROJECTS/Carbon-Crunch-Receipt-Intelligence")
PROJECT_ROOT = Path(__file__).parent.parent.parent if "__file__" in dir() else _PROJECT_ROOT_HARD

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLES_DIR = DATA_DIR / "samples"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "outputs"
RECEIPTS_DIR = OUTPUT_DIR / "receipts"
LOGS_DIR = OUTPUT_DIR / "logs"
EXPENSE_SUMMARY_PATH = OUTPUT_DIR / "expense_summary.json"
EVALUATION_REPORT_PATH = OUTPUT_DIR / "evaluation_report.json"

# Cache directory
CACHE_DIR = PROJECT_ROOT / ".cache"

# OCR configuration
OCR_LANG = "en"
OCR_USE_GPU = False  # Set to True if GPU available
OCR_SCALE = 1.0

# Confidence engine defaults
CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "ocr_confidence": 0.5,
    "pattern_validation": 0.2,
    "keyword_context": 0.15,
    "spatial_evidence": 0.15,
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    "high": 0.85,
    "medium": 0.70,
    "low": 0.0,
}

# Field statuses
FIELD_STATUSES = ["HIGH_CONFIDENCE", "MEDIUM_CONFIDENCE", "LOW_CONFIDENCE", "MISSING", "CONFLICT"]

# Image processing
MAX_DIMENSION = 2000  # Max width/height in pixels for resizing
MIN_DIMENSION = 200   # Min width/height in pixels
DEFAULT_SCALE_FACTOR = 2.0  # Scale for preprocessing variants

# File extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

# Logging
LOG_FILE = LOGS_DIR / "pipeline.log"