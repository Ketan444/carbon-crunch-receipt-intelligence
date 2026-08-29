# -*- coding: utf-8 -*-
"""Item and price extraction from receipt OCR text."""

import re
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from .schemas import ExtractedField, FieldStatus, ReceiptItem


def extract_store_name(
    ocr_results: List[tuple],
    image_height: int,
    image_width: int,
) -> ExtractedField:
    """Extract store name from receipt headers.

    Look mainly in the top portion of the receipt (header region).
    Use position, OCR confidence, and exclusion rules.

    Args:
        ocr_results: List of (text, confidence, bounding_box) from OCR
        image_height: Height of the original image in pixels
        image_width: Width of the original image in pixels

    Returns:
        ExtractedField with store name and confidence
    """
    if not ocr_results:
        return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)

    # Focus on header region (top 15-25% of image)
    header_y_threshold = image_height * 0.25

    # Filter text lines in the header region
    header_texts = []
    for text, confidence, bbox in ocr_results:
        # Get the y-coordinate of the bounding box
        # bbox is list of (x, y) points
        if len(bbox) >= 2:
            min_y = min(point[1] for point in bbox)
            if min_y < header_y_threshold:
                header_texts.append((text, confidence, bbox))

    if not header_texts:
        return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)

    # Exclusion rules - skip lines that look like addresses, phone, tax ID
    excluded_keywords = [
        "phone", "tel", "fax", "address", "addr", "street", "suite",
        "vat", "tax id", "gst", "hst", "copyright", "all rights reserved",
    ]

    filtered_texts = []
    for text, confidence, bbox in header_texts:
        text_lower = text.lower()
        if not any(kw in text_lower for kw in excluded_keywords):
            filtered_texts.append((text, confidence, bbox))

    if not filtered_texts:
        # If all texts were excluded, still try to find the best candidate
        filtered_texts = header_texts[:3]

    # Exclusion: skip long lines (likely addresses) and lines with special chars density
    valid_texts = []
    for text, confidence, bbox in filtered_texts:
        # Skip if line is very long (likely address)
        if len(text) > 80:
            continue
        # Skip if too many special characters
        special_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_ratio > 0.4:
            continue
        valid_texts.append((text, confidence, bbox))

    if not valid_texts:
        return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)

    # Sort by confidence, then by position (left to right)
    valid_texts.sort(key=lambda x: (x[1], x[2][0][0]), reverse=True)

    # Take the best candidate
    best_text, best_confidence, best_bbox = valid_texts[0]

    # Additional check: the store name should be relatively short
    if len(best_text) > 100:
        return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)

    # Clean the text
    store_name = best_text.strip()

    # Build confidence from OCR confidence and position evidence
    adjusted_confidence = min(best_confidence * 0.9 + 0.1, 1.0)

    return ExtractedField(
        value=store_name,
        confidence=round(adjusted_confidence, 4),
        status=FieldStatus.HIGH_CONFIDENCE if adjusted_confidence >= 0.85 else FieldStatus.MEDIUM_CONFIDENCE,
    )


# Items that look like store headers/footers should be excluded
STORE_HEADER_KEYWORDS = {
    "wal", "supercenter", "market", "store", "pharmacy", "discount",
    "mart", "center", "mega", "price", "extra", "value", "convenience",
    "express", "depot", "commercial", "plaza", "galleria",
}

# Common footer/footer keywords
FOOTER_KEYWORDS = {
    "tax", "subtotal", "total", "change", "cash", "card", "amount due",
    "balance", "receipt", "date", "time", "copyright", "all rights reserved",
    "void", "refund", "credit", "gift card", "limit", "void",
}
def is_excluded_keyword(text: str) -> bool:
    """Check if text matches an excluded keyword pattern."""
    text_lower = text.lower().strip()

    # Check exact match against footer keywords
    if text_lower in FOOTER_KEYWORDS:
        return True

    # Check if text starts with excluded keyword followed by number
    for kw in FOOTER_KEYWORDS:
        if text_lower.startswith(kw + " ") or text_lower == kw:
            return True

    return False

def extract_items(
    ocr_results: List[tuple],
    image_height: int,
    image_width: int,
) -> List[ReceiptItem]:
    """Extract items with prices from receipt OCR text.

    Use a hybrid method: OCR + regex + keywords + bounding boxes +
    line grouping + spatial relationships + context + validation.

    Args:
        ocr_results: List of (text, confidence, bounding_box) from OCR
        image_height: Height of the original image in pixels
        image_width: Width of the original image in pixels

    Returns:
        List of ReceiptItem objects
    """
    if not ocr_results:
        return []

    # Group OCR text into lines based on spatial positioning
    lines = _group_ocr_into_lines(ocr_results, image_width)

    # Extract item-price pairs from lines
    items = []
    seen_names = set()  # Basic dedup

    for line in lines:
        line_items = _extract_items_from_line(line)
        for item in line_items:
            # Basic dedup by name (case-insensitive)
            name_lower = item["name"].lower().strip()
            if name_lower in seen_names:
                continue
            if is_excluded_keyword(item["name"]):
                continue
            # Exclude store header/footer keywords
            name_lower_no_punct = ''.join(c for c in name_lower if c.isalnum())
            if any(name_lower_no_punct.startswith(kw) or name_lower == kw for kw in STORE_HEADER_KEYWORDS):
                continue
            if any(kw in name_lower for kw in FOOTER_KEYWORDS):
                continue
            if not item["name"] or item["price"] == "0.00":
                continue
            seen_names.add(name_lower)
            items.append(ReceiptItem(
                name=item["name"].strip(),
                price=item["price"],
                confidence=item["confidence"],
            ))

    # Sort items by position (top to bottom, left to right)
    items.sort(key=lambda x: (x.confidence,))  # Sort by confidence primarily

    return items


def _group_ocr_into_lines(
    ocr_results: List[tuple],
    image_width: int,
    y_tolerance: int = 10,
) -> List[List[tuple]]:
    """Group OCR results into horizontal lines based on y-position."""
    if not ocr_results:
        return []

    # Sort by y-coordinate (top to bottom), then x-coordinate (left to right)
    sorted_results = sorted(ocr_results, key=lambda r: (r[2][1] if len(r[2]) > 1 else 0, r[2][0] if len(r[2]) > 0 else 0))

    lines = []
    if not sorted_results:
        return lines

    current_line = [sorted_results[0]]

    for result in sorted_results[1:]:
        text, conf, bbox = result
        last_text, last_conf, last_bbox = current_line[-1]

        # Get y-centers
        last_y_center = (last_bbox[0][1] + last_bbox[2][1]) / 2 if len(last_bbox) > 2 else last_bbox[0][1]
        y_center = (bbox[0][1] + bbox[2][1]) / 2 if len(bbox) > 2 else bbox[0][1]

        # Check if on same line
        y_diff = abs(y_center - last_y_center)

        if y_diff <= y_tolerance:
            # Same line - add to current line
            current_line.append(result)
        else:
            # Different line - start new line
            lines.append(current_line)
            current_line = [result]

    # Don't forget the last line
    if current_line:
        lines.append(current_line)

    return lines


def _extract_items_from_line(
    line_results: List[tuple],
) -> List[Dict[str, Any]]:
    """Extract item-name and price from a single line of OCR text.

    Example line: "Milk       45.00"
    """
    if not line_results:
        return []

    items = []

    # Join all text from the line
    all_text = " ".join(result[0] for result in line_results)

    # Split by common delimiters and reconstruct
    # Try to find pattern: item_name followed by price
    # Multiple strategies:

    # Strategy 1: Split by whitespace and find price at end
    words = all_text.split()

    if not words:
        return items

    # Look for price patterns in the text
    price_idx = -1
    price_value = None

    for i, word in enumerate(words):
        price_candidate = _is_price(word)
        if price_candidate is not None:
            price_idx = i
            price_value = price_candidate
            break

    if price_idx >= 0 and price_value is not None:
        # Everything before the price is the item name
        name_parts = words[:price_idx]
        name = " ".join(name_parts).strip()

        # Remove trailing zeros and clean
        if name and price_value:
            items.append({
                "name": name,
                "price": price_value,
                "confidence": _calculate_line_confidence(line_results),
            })
    else:
        # No clear price at end - try splitting by known patterns
        # Check if entire line looks like "Item 45.00"
        for i, word in enumerate(words):
            if _is_price(word):
                # This word might be a price, check if there's a name before it
                name_part = " ".join(words[:i]).strip()
                if name_part and not is_excluded_keyword(name_part):
                    try:
                        float(word)
                        # This looks like item + price
                        items.append({
                            "name": name_part,
                            "price": word,
                            "confidence": _calculate_line_confidence(line_results),
                        })
                    except ValueError:
                        pass

    return items


def _is_price(text: str) -> Optional[str]:
    """Check if text represents a price value."""
    # Pattern: 45.00, 45,00, $45.00
    price_patterns = [
        r'^\$?\d{1,3}(?:[,\.]\d{2})?$',
        r'^\d{1,3}(?:[,\.]\d{2})?$',
        r'^\d+\.\d{2}$',
        r'^\d{1,3},\d{2}$',
    ]

    for pattern in price_patterns:
        if re.match(pattern, text.strip()):
            # Validate numeric value
            clean = text.strip().replace('$', '').replace(',', '.')
            try:
                val = float(clean)
                if 0.01 <= val <= 100000.0:
                    return text.strip()
            except ValueError:
                continue
    return None


def _calculate_line_confidence(line_results: List[tuple]) -> float:
    """Calculate confidence for a line of OCR text."""
    if not line_results:
        return 0.0

    # Average confidence of all text elements in the line
    confidences = [result[1] for result in line_results if len(result) > 1]
    if confidences:
        return round(sum(confidences) / len(confidences), 4)
    return 0.5


def extract_prices_from_text(
    ocr_text: str,
) -> List[Dict[str, Any]]:
    """Extract all price values from OCR text.

    Returns list of dicts with price and confidence.
    """
    if not ocr_text or not ocr_text.strip():
        return []

    prices = []
    # Find all currency/price patterns
    price_patterns = [
        r'[$€£¥₹]?\s*(\d{1,3}(?:[,\.]\d{2})?(?:\s+\d{1,3}(?:[,\.]\d{2})?)?)',
        r'(\d{1,3}(?:[,\.]\d{2})?(?:\s+\d{1,3}(?:[,\.]\d{2})?)?)',
    ]

    for pattern in price_patterns:
        matches = re.finditer(pattern, ocr_text)
        for match in matches:
            value_str = match.group(0)
            # Clean and validate
            clean = value_str.strip().replace(',', '.')
            try:
                val = float(clean)
                if 0.01 <= val <= 100000.0:
                    # Determine currency
                    has_currency = bool(re.search(r'[$€£¥₹]', value_str))
                    prices.append({
                        "value": value_str.strip(),
                        "numeric_value": round(val, 2),
                        "has_currency": has_currency,
                        "confidence": 0.7,
                    })
            except ValueError:
                continue

    # Deduplicate by numeric value
    seen = set()
    deduped = []
    for p in prices:
        key = p["numeric_value"]
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    return deduped


# Export all functions
__all__ = [
    "extract_items",
    "extract_prices_from_text",
    "is_excluded_keyword",
    "_group_ocr_into_lines",
    "_extract_items_from_line",
    "_is_price",
    "_calculate_line_confidence",
]