# -*- coding: utf-8 -*-
"""Total amount extraction from receipt OCR text."""

import re
from typing import List, Optional, Dict, Any, Tuple
from .schemas import ExtractedField, FieldStatus
from .ocr_normalization import extract_price_from_text


# Context keywords for total detection with their strengths
TOTAL_KEYWORDS = {
    "grand_total": 0.95,
    "total": 0.90,
    "amount_due": 0.85,
    "balance": 0.80,
    "net_total": 0.75,
    "subtotal": 0.40,  # Lower - could be subtotal not total
    "total_amount": 0.85,
}


def extract_total(
    ocr_text: str,
    all_prices: List[Dict[str, Any]],
    ocr_confidence: float = 1.0,
) -> ExtractedField:
    """Extract total amount from receipt OCR text.

    Prioritize contextual keywords such as:
    - TOTAL, GRAND TOTAL, AMOUNT DUE, BALANCE, NET TOTAL

    Use:
    - keyword strength
    - currency pattern
    - position
    - OCR confidence
    - context
    - arithmetic consistency

    DO NOT simply choose:
    - largest number
    - last number
    - first number

    Generate candidates and rank them.
    """
    if not ocr_text and not all_prices:
        return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)

    # Generate candidate totals from multiple sources
    candidates = _generate_total_candidates(
        ocr_text, all_prices, ocr_confidence
    )

    if not candidates:
        # Fallback: try to find any large price-like number
        return _fallback_total_extraction(all_prices)

    # Rank candidates and return the best one
    best = _rank_total_candidates(candidates)

    # Convert to ExtractedField
    value = best.get("value")
    confidence = best.get("confidence", 0.0)
    status = (
        FieldStatus.HIGH_CONFIDENCE
        if confidence >= 0.85
        else FieldStatus.MEDIUM_CONFIDENCE
        if confidence >= 0.70
        else FieldStatus.LOW_CONFIDENCE
    )

    return ExtractedField(
        value=value,
        confidence=round(confidence, 4),
        status=status,
    )


def _generate_total_candidates(
    ocr_text: str,
    all_prices: List[Dict[str, Any]],
    ocr_confidence: float,
) -> List[Dict[str, Any]]:
    """Generate total candidates from various sources."""
    candidates = []

    if not ocr_text:
        return candidates

    text = ocr_text.lower()

    # Source 1: Contextual keywords
    for keyword, strength in TOTAL_KEYWORDS.items():
        # Match whole word or phrase
        patterns = [
            rf'\b{keyword}\b',
            rf'{keyword}\s+[\d,\.]+',
            rf'[\d,\.]+\s*{keyword}',
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract associated number
                start = match.start()
                end = match.end()
                # Look for number after or before
                associated_text = text[start:end]

                # Find number in the matched region
                number_match = re.search(r'[\d,\.]+', associated_text)
                if number_match:
                    value_str = number_match.group(0).replace(',', '.')
                    try:
                        val = float(value_str)
                        if 10 <= val <= 1000000:  # Reasonable total range
                            candidates.append({
                                "value": f"{val:.2f}",
                                "keyword": keyword,
                                "keyword_strength": strength,
                                "position": start,
                                "ocr_confidence": ocr_confidence,
                                "confidence": round(strength * ocr_confidence, 4),
                            })
                    except ValueError:
                        pass

    # Source 2: Largest price from item prices (arithmetic consistency)
    if all_prices:
        # Sum of all item prices
        price_values = []
        for p in all_prices:
            try:
                val = float(p.get("numeric_value", p.get("value", 0)))
                price_values.append(val)
            except (ValueError, TypeError):
                continue

        if price_values:
            # Candidate: sum of all prices
            total_sum = sum(price_values)
            if 10 <= total_sum <= 1000000:
                candidates.append({
                    "value": f"{total_sum:.2f}",
                    "source": "sum_of_item_prices",
                    "keyword_strength": 0.3,
                    "position": 0,
                    "ocr_confidence": ocr_confidence,
                    "confidence": round(0.3 * ocr_confidence, 4),
                    "arithmetic_consistency": True,
                    "method": "sum",
                })

            # Candidate: largest individual price (could be total if single item)
            max_price = max(price_values)
            if max_price > 50:  # Heuristic: total is usually not a single small item
                candidates.append({
                    "value": f"{max_price:.2f}",
                    "source": "largest_item_price",
                    "keyword_strength": 0.1,
                    "position": 0,
                    "ocr_confidence": ocr_confidence,
                    "confidence": round(0.1 * ocr_confidence, 4),
                    "arithmetic_consistency": False,
                    "method": "max",
                })

    # Source 3: Any price-like number near "total" keywords
    if ocr_text:
        # Look for numbers that appear after total keywords
        for keyword in TOTAL_KEYWORDS.keys():
            keyword_pattern = rf'\b{keyword}\b\s+[\d,\.]+'
            matches = re.finditer(keyword_pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract the number that follows
                after_keyword = text[match.end():match.end() + 30]
                number_match = re.search(r'[\d,\.]+', after_keyword)
                if number_match:
                    value_str = number_match.group(0).replace(',', '.')
                    try:
                        val = float(value_str)
                        if 10 <= val <= 1000000:
                            candidates.append({
                                "value": f"{val:.2f}",
                                "keyword": keyword,
                                "keyword_strength": TOTAL_KEYWORDS[keyword],
                                "position": match.start(),
                                "ocr_confidence": ocr_confidence,
                                "confidence": round(TOTAL_KEYWORDS[keyword] * ocr_confidence, 4),
                            })
                    except ValueError:
                        pass

    return candidates


def _rank_total_candidates(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rank total candidates and return the best one.

    Ranking criteria:
    1. Keyword strength (strongest keyword = highest priority)
    2. Arithmetic consistency (sum of prices vs standalone number)
    3. OCR confidence
    4. Position in document
    """
    if not candidates:
        return {"value": None, "confidence": 0.0}

    # Add composite scoring
    for c in candidates:
        score = 0.0

        # Keyword strength (base)
        score += c.get("keyword_strength", 0) * 0.4

        # Arithmetic consistency bonus
        if c.get("arithmetic_consistency"):
            score += 0.3

        # OCR confidence weight
        score += c.get("ocr_confidence", 0.5) * 0.2

        # Position preference (earlier in document = slightly better)
        # Position is already factored into confidence, but add small bonus
        # for being found near total keywords

        c["total_score"] = score

    # Return the highest-scoring candidate
    best = max(candidates, key=lambda c: c.get("total_score", 0))

    return best


def _fallback_total_extraction(
    all_prices: List[Dict[str, Any]],
) -> ExtractedField:
    """Fall back to extracting total from available prices."""
    if not all_prices:
        return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)

    # Try sum of all prices
    price_values = []
    for p in all_prices:
        try:
            val = float(p.get("numeric_value", p.get("value", 0)))
            price_values.append(val)
        except (ValueError, TypeError):
            continue

    if price_values:
        total = sum(price_values)
        if total > 0:
            return ExtractedField(
                value=f"{total:.2f}",
                confidence=0.4,  # Low confidence for fallback
                status=FieldStatus.MEDIUM_CONFIDENCE,
            )

    # Last resort: largest price
    try:
        max_val = max(price_values)
        if max_val > 0:
            return ExtractedField(
                value=f"{max_val:.2f}",
                confidence=0.2,
                status=FieldStatus.LOW_CONFIDENCE,
            )
    except (ValueError, TypeError):
        pass

    return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)


# Export all functions
__all__ = [
    "extract_total",
    "_generate_total_candidates",
    "_rank_total_candidates",
    "_fallback_total_extraction",
]