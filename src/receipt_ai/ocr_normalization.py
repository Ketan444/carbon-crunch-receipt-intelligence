# -*- coding: utf-8 -*-
"""OCR result normalization and text processing."""

import re
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path


def normalize_whitespace(text: str) -> str:
    """Normalize excessive whitespace in OCR output."""
    # Replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    # Strip leading/trailing whitespace on lines
    lines = [line.strip() for line in text.split('\n')]
    # Strip overall
    text = '\n'.join(lines)
    text = text.strip()
    return text


def clean_currency_symbols(text: str) -> str:
    """Clean currency symbols from text while preserving representation."""
    # Common currency symbols that OCR may pick up
    symbols = ['$', '₹', '€', '£', '¥', '₽', '₩', '₡', '₦', '₱']
    for symbol in symbols:
        text = text.replace(symbol, '')
    return text


def extract_currency_and_value(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract currency symbol and numeric value from text."""
    # Pattern for currency values: $45.00, ₹45.00, 45.00, 45,00
    currency_patterns = [
        (r'[$€£¥₹₽₩₡₦₱]\s*([\d,]+\.?\d*)', "symbol_first"),
        (r'([\d,]+\.?\d*)\s*[$€£¥₹₽₩₡₦₱]', "symbol_last"),
        (r'([\d,]+\.?\d*)', "no_symbol"),
    ]

    for pattern, kind in currency_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).replace(',', '')
            if kind == "symbol_first":
                symbol = pattern[0]  # Simplified
                return (symbol, value)
            elif kind == "symbol_last":
                return ("", value)
            else:
                return ("", value)

    return (None, None)


def normalize_ocr_text(text: str) -> str:
    """Full normalization pipeline for OCR text."""
    # Normalize whitespace
    text = normalize_whitespace(text)
    # Clean currency symbols for parsing but keep original for display
    text_clean = clean_currency_symbols(text)
    return text_clean


def group_text_lines(
    ocr_results: List[tuple],
    x_tolerance: int = 20,
    y_tolerance: int = 5,
) -> List[List[Tuple[str, float, Tuple[int, int, int, int]]]]:
    """Group OCR text lines into rows based on spatial positioning.

    Args:
        ocr_results: List of (text, confidence, (x, y)) tuples
        x_tolerance: Maximum x-difference to consider texts on same line
        y_tolerance: Maximum y-difference to consider texts on same line

    Returns:
        List of rows, each row is a list of (text, confidence, (x1, y1, x2, y2))
    """
    if not ocr_results:
        return []

    # Sort by y-coordinate first, then x
    sorted_results = sorted(ocr_results, key=lambda r: (r[2][1], r[2][0]))

    rows = []
    current_row = [sorted_results[0]]

    for result in sorted_results[1:]:
        text, conf, (x, y) = result
        last_text, last_conf, (last_x, last_y, last_x2, last_y2) = current_row[-1]

        # Check if this result is on the same line as the last in current row
        y_diff = abs(y - last_y)

        if y_diff <= y_tolerance:
            # Same line - add to current row
            current_row.append(result)
        else:
            # Different line - start new row
            rows.append(current_row)
            current_row = [result]

    # Don't forget the last row
    if current_row:
        rows.append(current_row)

    return rows


def extract_price_from_text(text: str) -> Optional[str]:
    """Extract price from a text string using various patterns."""
    # Clean the text first
    text = text.strip()

    # Pattern: 45.00, 45,00, $45.00, ₹45.00
    price_patterns = [
        r'[$€£¥₹]?\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)',  # With currency
        r'(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)',  # Without currency
        r'(\d+\.\d{2})',  # Standard decimal
        r'(\d{1,3},\d{2})',  # Comma decimal (European)
    ]

    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).replace(',', '.')
            # Validate it's a reasonable price
            try:
                float_val = float(value)
                if 0.01 <= float_val <= 100000.0:
                    return value
            except ValueError:
                continue

    return None


def extract_date_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract potential dates from OCR text.

    Returns list of date candidates with value and format hints.
    """
    import datetime

    candidates = []
    text_upper = text.upper()

    # Common date patterns
    date_patterns = [
        (r'(\d{2})/(\d{2})/(\d{4})', "MM/DD/YYYY", "%m/%d/%Y"),
        (r'(\d{2})/(\d{2})/(\d{2})', "YY/MM/DD", "%y/%m/%d"),
        (r'(\d{4})-(\d{2})-(\d{2})', "YYYY-MM-DD", "%Y-%m-%d"),
        (r'(\d{2})-(\d{2})-(\d{4})', "DD-MM-YYYY", "%d-%m-%Y"),
        (r'(\d{2})\.(\d{2})\.(\d{4})', "DD.MM.YYYY", "%d.%m.%Y"),
        (r'(\d{2})-([A-Za-z]{3})-(\d{4})', "DD-Mon-YYYY", None),
    ]

    for pattern, fmt_alias, strptime_fmt in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                if strptime_fmt:
                    if '/' in pattern.split('/')[0] if '/' in pattern else '-':
                        pass
                    parsed = datetime.datetime.strptime(
                        '/'.join(match) if '/' in pattern.split('/')[0] else '-'.join(match),
                        strptime_fmt
                    )
                else:
                    # Month name format
                    day, month_name, year = match
                    month_map = {
                        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
                        'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
                        'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
                    }
                    month = month_map.get(month_name.upper())
                    if month:
                        parsed = datetime.datetime(int(year), month, int(day))

                # Validate the date is reasonable (not too far in past/future)
                year = parsed.year
                current_year = datetime.datetime.now().year
                if 2000 <= year <= current_year + 1:
                    candidates.append({
                        "value": parsed.strftime("%Y-%m-%d"),
                        "format": fmt_alias,
                        "original_text": match if isinstance(match, str) else '/'.join(match),
                        "confidence": 0.8,  # Base confidence for parsed dates
                    })
            except (ValueError, OverflowError, IndexError):
                continue

    # Deduplicate by value
    seen = set()
    deduped = []
    for c in candidates:
        if c["value"] not in seen:
            seen.add(c["value"])
            deduped.append(c)

    return deduped