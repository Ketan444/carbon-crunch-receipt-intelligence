# -*- coding: utf-8 -*-
"""Utility functions for Carbon Crunch Receipt Intelligence."""

import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path


def safe_json_load(filepath: Path) -> Any:
    """Safely load JSON from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def safe_json_dump(data: Any, filepath: Path, indent: int = 2) -> bool:
    """Safely dump JSON to a file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (IOError, TypeError):
        return False


def extract_receipt_id_from_filename(filename: str) -> str:
    """Extract receipt ID from filename.

    Handles various naming conventions:
    - receipt_001.jpg -> receipt_001
    - image_001.png -> image_001
    - scan_001.tiff -> scan_001
    - 001.jpg -> 001
    """
    # Remove extension
    name = Path(filename).stem

    # Common prefixes to strip
    prefixes = ["receipt_", "receipt-", "image_", "scan_", "receipt_"]
    for prefix in prefixes:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break

    # Clean up any remaining non-standard characters
    name = re.sub(r'[_\s-]+', '_', name)
    name = name.strip("_")

    # Ensure we have a meaningful ID
    if not name:
        name = "unknown_receipt"

    return name


def format_currency(value: float, symbol: str = "") -> str:
    """Format a numeric value as currency string."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "0.00"
    return f"{symbol}{value:.2f}"


def validate_json_schema(data: dict, schema_name: str = "receipt") -> bool:
    """Validate data against a basic schema."""
    # Basic validation - check required keys exist
    if schema_name == "receipt":
        required_keys = ["receipt_id", "source_image"]
        return all(k in data for k in required_keys)
    return True


def clean_ocr_text(text: str) -> str:
    """Clean OCR output text."""
    if not text:
        return ""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip
    text = text.strip()
    return text


# Export
__all__ = [
    "safe_json_load",
    "safe_json_dump",
    "extract_receipt_id_from_filename",
    "format_currency",
    "validate_json_schema",
    "clean_ocr_text",
]