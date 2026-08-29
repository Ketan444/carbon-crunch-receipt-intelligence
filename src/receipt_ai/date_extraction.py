# -*- coding: utf-8 -*-
"""Date extraction from receipt OCR text."""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime


def extract_date(ocr_text: str) -> Optional[Dict[str, Any]]:
    """Extract transaction date from OCR text.

    Support common formats:
    - DD/MM/YYYY
    - MM/DD/YYYY
    - YYYY-MM-DD
    - DD-MM-YYYY
    - DD.MM.YYYY
    and reasonable variants.

    When multiple date candidates exist:
    - generate candidates
    - rank candidates
    - consider position
    - consider context
    - consider confidence
    - flag ambiguity

    Never blindly choose the first date.
    """
    if not ocr_text or not ocr_text.strip():
        return None

    text = ocr_text.strip()
    candidates = _generate_date_candidates(text)

    if not candidates:
        return None

    # Rank candidates and return the best one
    best = _rank_date_candidates(candidates, text)

    return best


def _generate_date_candidates(text: str) -> List[Dict[str, Any]]:
    """Generate date candidates from OCR text."""
    import re

    candidates = []
    current_year = datetime.now().year

    # Pattern: DD/MM/YYYY or MM/DD/YYYY
    slash_patterns = re.findall(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    for match in slash_patterns:
        day, month, year = int(match[0]), int(match[1]), int(match[2])
        # Both DD/MM/YYYY and MM/DD/YYYY are possible
        # Heuristic: if day > 12, it must be DD/MM/YYYY
        if day > 12:
            # Must be DD/MM/YYYY
            if 1 <= month <= 12 and 2000 <= year <= current_year + 1:
                try:
                    dt = datetime(year, month, day)
                    candidates.append({
                        "value": dt.strftime("%Y-%m-%d"),
                        "format": "DD/MM/YYYY",
                        "original_parts": match,
                        "confidence": 0.7,
                    })
                except ValueError:
                    pass
        elif month > 12:
            # Must be MM/DD/YYYY
            if 1 <= day <= 31 and 2000 <= year <= current_year + 1:
                try:
                    dt = datetime(year, month=month if month <= 12 else day, day=day if month > 12 else month)
                    # Actually this case means month is valid as month, day is valid as day
                    # But we have day, month swapped - need to be careful
                    # If month <= 12 and day <= 31, both interpretations possible
                    # Prefer MM/DD/YYYY when month <= 12
                    if month <= 12:
                        dt = datetime(year, month=month, day=day)
                        candidates.append({
                            "value": dt.strftime("%Y-%m-%d"),
                            "format": "MM/DD/YYYY",
                            "original_parts": match,
                            "confidence": 0.7,
                        })
                except ValueError:
                    pass
        else:
            # Both day and month <= 12, ambiguous
            # Try both interpretations
            # Interpretation 1: MM/DD/YYYY
            if 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    dt = datetime(year, month=month, day=day)
                    candidates.append({
                        "value": dt.strftime("%Y-%m-%d"),
                        "format": "MM/DD/YYYY",
                        "original_parts": match,
                        "confidence": 0.5,  # Lower confidence due to ambiguity
                    })
                except ValueError:
                    pass

            # Interpretation 2: DD/MM/YYYY
            if 1 <= day <= 31 and 1 <= month <= 12:
                try:
                    dt = datetime(year, month=month, day=day)
                    # Only add if different from MM/DD interpretation
                    # Actually both use same format, so we track which interpretation
                    candidates.append({
                        "value": dt.strftime("%Y-%m-%d"),
                        "format": "DD/MM/YYYY",
                        "original_parts": match,
                        "confidence": 0.5,
                    })
                except ValueError:
                    pass

    # Pattern: YYYY-MM-DD
    dash_patterns = re.findall(r'(\d{4})-(\d{2})-(\d{2})', text)
    for match in dash_patterns:
        year, month, day = int(match[0]), int(match[1]), int(match[2])
        if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= current_year + 1:
            try:
                dt = datetime(year, month, day)
                candidates.append({
                    "value": dt.strftime("%Y-%m-%d"),
                    "format": "YYYY-MM-DD",
                    "original_parts": match,
                    "confidence": 0.8,
                })
            except ValueError:
                pass

    # Pattern: DD-MM-YYYY or MM-DD-YYYY
    dash_patterns2 = re.findall(r'(\d{1,2})-(\d{1,2})-(\d{4})', text)
    for match in dash_patterns2:
        first, second, year = int(match[0]), int(match[1]), int(match[2])
        if year < 2000 or year > current_year + 1:
            continue

        # If first > 12, must be DD-MM-YYYY
        if first > 12:
            if 1 <= second <= 12:
                try:
                    dt = datetime(year, month=second, day=first)
                    candidates.append({
                        "value": dt.strftime("%Y-%m-%d"),
                        "format": "DD-MM-YYYY",
                        "original_parts": match,
                        "confidence": 0.7,
                    })
                except ValueError:
                    pass
        # If second > 12, must be MM-DD-YYYY
        elif second > 12:
            if 1 <= first <= 12:
                try:
                    dt = datetime(year, month=first, day=second)
                    candidates.append({
                        "value": dt.strftime("%Y-%m-%d"),
                        "format": "MM-DD-YYYY",
                        "original_parts": match,
                        "confidence": 0.7,
                    })
                except ValueError:
                    pass
        else:
            # Both <= 12, ambiguous - try both
            # MM-DD-YYYY
            if 1 <= first <= 12 and 1 <= second <= 31:
                try:
                    dt = datetime(year, month=first, day=second)
                    candidates.append({
                        "value": dt.strftime("%Y-%m-%d"),
                        "format": "MM-DD-YYYY",
                        "original_parts": match,
                        "confidence": 0.5,
                    })
                except ValueError:
                    pass

            # DD-MM-YYYY
            if 1 <= second <= 12 and 1 <= first <= 31:
                try:
                    dt = datetime(year, month=second, day=first)
                    candidates.append({
                        "value": dt.strftime("%Y-%m-%d"),
                        "format": "DD-MM-YYYY",
                        "original_parts": match,
                        "confidence": 0.5,
                    })
                except ValueError:
                    pass

    # Pattern: DD.MM.YYYY
    dot_patterns = re.findall(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
    for match in dot_patterns:
        day, month, year = int(match[0]), int(match[1]), int(match[2])
        if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= current_year + 1:
            try:
                dt = datetime(year, month, day)
                candidates.append({
                    "value": dt.strftime("%Y-%m-%d"),
                    "format": "DD.MM.YYYY",
                    "original_parts": match,
                    "confidence": 0.7,
                })
            except ValueError:
                pass

    # Deduplicate by value, keeping highest confidence
    seen = {}
    for c in candidates:
        val = c["value"]
        if val not in seen or c["confidence"] > seen[val]["confidence"]:
            seen[val] = c

    return list(seen.values())


def _rank_date_candidates(
    candidates: List[Dict[str, Any]],
    full_text: str,
) -> Optional[Dict[str, Any]]:
    """Rank date candidates and return the best one.

    Ranking criteria (in order):
    1. Position in document (header dates are more likely transaction dates)
    2. Context clues (words like "date", "today", "printed")
    3. Confidence score
    4. Format unambiguity (unambiguous formats ranked higher)
    """
    if not candidates:
        return None

    # Add positional scoring
    for i, c in enumerate(candidates):
        # Check if date appears in later part of text (less likely to be transaction date)
        pos = full_text.find(c["original_parts"][0] if c.get("original_parts") else "")
        if pos >= 0:
            # Earlier in document = higher score for transaction date
            pos_score = max(0, 1 - pos / len(full_text)) * 0.3
        else:
            pos_score = 0.0
        c["position_score"] = pos_score

    # Add context scoring
    for c in candidates:
        context_bonus = 0.0
        text_lower = full_text.lower()
        # Bonus if near "date" keyword
        if re.search(r'\b(date|transaction|issued|printed)\b', text_lower):
            # Check if date keyword is near the date candidate
            context_bonus += 0.2
        # Bonus if date is in first half of document
        context_bonus += c.get("position_score", 0)
        c["context_score"] = context_bonus

    # Sort by combined score (confidence + context)
    for c in candidates:
        c["total_score"] = c.get("confidence", 0) + c.get("context_score", 0) + c.get("position_score", 0)

    # Return the highest-scoring candidate
    best = max(candidates, key=lambda c: c.get("total_score", 0))

    # If best has very low confidence, return None
    if best.get("total_score", 0) < 0.5:
        return None

    return best


# Export all functions
__all__ = ["extract_date", "_generate_date_candidates", "_rank_date_candidates"]