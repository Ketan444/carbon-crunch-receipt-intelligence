# -*- coding: utf-8 -*-
"""Validation module for extracted receipt data."""

import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .schemas import ExtractedField, FieldStatus, ReceiptItem, FinancialSummary, EvaluationResult
from .extraction import is_excluded_keyword


def validate_date(field: ExtractedField) -> ExtractedField:
    """Validate an extracted date field.

    Returns the field with updated confidence/status based on validation.
    """
    if field is None or field.value is None:
        field.status = FieldStatus.MISSING
        field.confidence = 0.0
        return field

    value = str(field.value)

    # Check date format YYYY-MM-DD
    date_patterns = [
        r'^\d{4}-\d{2}-\d{2}$',
        r'^\d{2}/\d{2}/\d{4}$',
        r'^\d{2}-\d{2}-\d{4}$',
        r'^\d{2}\.\d{2}\.\d{4}$',
    ]

    is_valid_format = any(re.match(pattern, value) for pattern in date_patterns)

    if not is_valid_format:
        # Try to parse and reformat
        try:
            parsed = _try_parse_date(value)
            if parsed:
                field.value = parsed.strftime("%Y-%m-%d")
                field.confidence = field.confidence * 0.8  # Slightly reduced
                field.status = (
                    FieldStatus.HIGH_CONFIDENCE
                    if field.confidence >= 0.85
                    else FieldStatus.MEDIUM_CONFIDENCE
                )
                return field
        except Exception:
            pass

    if not is_valid_format:
        field.confidence = field.confidence * 0.5
        field.status = FieldStatus.LOW_CONFIDENCE

    return field


def _try_parse_date(value: str) -> Optional[datetime]:
    """Try to parse a date string."""
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def validate_currency(field: ExtractedField) -> ExtractedField:
    """Validate a currency/price field.

    Returns the field with updated confidence/status.
    """
    if field is None or field.value is None:
        field.status = FieldStatus.MISSING
        field.confidence = 0.0
        return field

    value = str(field.value)

    # Remove currency symbols for validation
    clean = re.sub(r'[$€£¥₹¥₽₩₡₦₱]', '', value)

    # Check if it's a valid number
    try:
        float_val = float(clean)
        if float_val < 0:
            # Negative values are unusual for receipt items (could be refund)
            field.confidence = field.confidence * 0.7
            field.status = FieldStatus.LOW_CONFIDENCE
        elif float_val == 0:
            field.confidence = field.confidence * 0.3
            field.status = FieldStatus.LOW_CONFIDENCE
        else:
            # Valid positive currency value
            field.confidence = min(field.confidence, 1.0)
            # Restore confidence if it was low due to OCR but value is valid
            if field.status == FieldStatus.LOW_CONFIDENCE:
                field.confidence = max(field.confidence, 0.7)
                field.status = (
                    FieldStatus.HIGH_CONFIDENCE
                    if field.confidence >= 0.85
                    else FieldStatus.MEDIUM_CONFIDENCE
                )
    except ValueError:
        field.confidence = field.confidence * 0.3
        field.status = FieldStatus.LOW_CONFIDENCE

    return field


def validate_items(items: List[ReceiptItem]) -> List[ReceiptItem]:
    """Validate extracted items.

    Returns list of valid items with updated confidence.
    """
    valid_items = []

    for item in items:
        if not item.name or item.name.strip() == "":
            continue  # Skip items without names

        if is_excluded_keyword(item.name):
            continue  # Skip excluded keywords

        # Validate price
        if item.price:
            clean_price = re.sub(r'[$€£¥₹]', '', item.price)
            try:
                float(clean_price)
            except ValueError:
                # Invalid price - reduce confidence
                item.confidence = item.confidence * 0.5
                # Keep item but mark as low confidence
                item.status = FieldStatus.LOW_CONFIDENCE

        # Check for reasonable price range
        if item.price:
            try:
                price_val = float(re.sub(r'[$€£¥₹]', '', item.price))
                if price_val < 0.01 or price_val > 100000:
                    # Unreasonable price - lower confidence
                    item.confidence = item.confidence * 0.5
            except ValueError:
                item.confidence = item.confidence * 0.5

        valid_items.append(item)

    return valid_items


def validate_arithmetic_consistency(
    receipt: dict,
) -> Dict[str, Any]:
    """Validate arithmetic consistency: sum of item prices vs total.

    Returns dict with consistency check results.
    """
    items = receipt.get("items", [])
    total_field = receipt.get("total_amount", {})

    item_prices = []
    for item in items:
        if item.price:
            try:
                item_prices.append(float(re.sub(r'[$€£¥₹]', '', item.price)))
            except ValueError:
                continue

    if not item_prices:
        return {
            "arithmetic_consistent": False,
            "item_sum": 0.0,
            "total_value": total_field.get("value"),
            "deviation": None,
            "consistency_ratio": None,
        }

    item_sum = sum(item_prices)

    if total_field.get("value") is not None:
        try:
            total_val = float(re.sub(r'[$€£¥₹]', '', total_field["value"]))
            if item_sum > 0:
                ratio = abs(item_sum - total_val) / max(item_sum, total_val, 1)
                deviation = abs(item_sum - total_val)
                consistent = ratio < 0.1  # Within 10% is consistent
            else:
                deviation = None
                ratio = None
                consistent = False
        except ValueError:
            deviation = None
            ratio = None
            consistent = False
    else:
        deviation = None
        ratio = None
        consistent = False

    return {
        "arithmetic_consistent": consistent,
        "item_sum": round(item_sum, 2),
        "total_value": total_field.get("value"),
        "deviation": round(deviation, 2) if deviation else None,
        "consistency_ratio": round(ratio, 4) if ratio else None,
        "item_count": len(item_prices),
    }


def validate_receipt(receipt: dict) -> dict:
    """Validate a complete receipt dict.

    Validates all fields and returns updated receipt with confidence adjustments.
    """
    # Validate date
    if receipt.get("date"):
        receipt["date"] = validate_date(receipt["date"])

    # Validate total amount
    if receipt.get("total_amount"):
        receipt["total_amount"] = validate_currency(receipt["total_amount"])

    # Validate items
    if receipt.get("items"):
        receipt["items"] = validate_items(receipt["items"])

    # Check arithmetic consistency
    arith_check = validate_arithmetic_consistency(receipt)

    # If arithmetic is inconsistent, reduce total confidence
    if not arith_check["arithmetic_consistent"] and receipt.get("total_amount", {}).get("confidence", 1.0) > 0:
        total_conf = receipt["total_amount"]["confidence"]
        receipt["total_amount"]["confidence"] = round(total_conf * 0.7, 4)
        # If too inconsistent, lower status
        if arith_check["consistency_ratio"] and arith_check["consistency_ratio"] > 0.3:
            if receipt["total_amount"]["status"] == "HIGH_CONFIDENCE":
                receipt["total_amount"]["status"] = "MEDIUM_CONFIDENCE"

    return receipt


# Export all functions
__all__ = [
    "validate_date",
    "validate_currency",
    "validate_items",
    "validate_arithmetic_consistency",
    "validate_receipt",
]