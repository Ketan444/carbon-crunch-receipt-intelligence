# -*- coding: utf-8 -*-
"""Confidence engine for receipt extraction fields."""

from typing import List, Dict, Any, Optional
from .schemas import ExtractedField, FieldStatus


def calculate_field_confidence(
    field: ExtractedField,
    evidence: Optional[Dict[str, Any]] = None,
) -> ExtractedField:
    """Calculate confidence for an extracted field.

    Combines:
    - OCR confidence
    - Pattern validation
    - Keyword/context evidence
    - Spatial evidence
    - Mathematical consistency where appropriate

    Initial configurable weights:
    - OCR confidence              = 50%
    - Pattern validation          = 20%
    - Keyword/context evidence    = 15%
    - Spatial evidence            = 15%

    These are starting values - experiment and tune if useful.

    Args:
        field: The ExtractedField to calculate confidence for
        evidence: Dict with evidence components (optional)

    Returns:
        Updated ExtractedField with confidence and status
    """
    if field is None:
        return field

    # Default evidence if none provided
    if evidence is None:
        evidence = _default_evidence(field)

    # Extract evidence values
    ocr_conf = evidence.get("ocr_confidence", field.confidence)
    pattern_valid = evidence.get("pattern_valid", False)
    keyword_match = evidence.get("keyword_match", False)
    spatial_score = evidence.get("spatial_score", 0.5)

    # Apply configurable weights
    weights = {
        "ocr_confidence": 0.5,
        "pattern_validation": 0.2,
        "keyword_context": 0.15,
        "spatial_evidence": 0.15,
    }

    # Calculate combined confidence
    combined = (
        weights["ocr_confidence"] * ocr_conf +
        weights["pattern_validation"] * (1.0 if pattern_valid else 0.0) +
        weights["keyword_context"] * (1.0 if keyword_match else 0.0) +
        weights["spatial_evidence"] * spatial_score
    )

    # Clamp to [0, 1]
    combined = max(0.0, min(1.0, combined))

    # Update field confidence
    field.confidence = round(combined, 4)

    # Determine status based on thresholds
    thresholds = {
        "high": 0.85,
        "medium": 0.70,
    }

    if combined >= thresholds["high"]:
        field.status = FieldStatus.HIGH_CONFIDENCE
    elif combined >= thresholds["medium"]:
        field.status = FieldStatus.MEDIUM_CONFIDENCE
    else:
        field.status = FieldStatus.LOW_CONFIDENCE

    return field


def _default_evidence(field: ExtractedField) -> Dict[str, Any]:
    """Generate default evidence for a field.

    This is a placeholder - real evidence comes from each extraction module.
    """
    # Use field's current confidence as OCR confidence proxy
    ocr_conf = field.confidence

    # Default assessments - these would be computed from actual data
    pattern_valid = field.confidence > 0.5  # Simplified check
    keyword_match = False  # Would be set by extraction module
    spatial_score = 0.5  # Would be set by extraction module

    return {
        "ocr_confidence": ocr_conf,
        "pattern_valid": pattern_valid,
        "keyword_match": keyword_match,
        "spatial_score": spatial_score,
    }


def calculate_items_confidence(
    items: List[ExtractedField],
) -> List[ExtractedField]:
    """Calculate confidence for multiple extracted fields (e.g., items).

    For items, confidence may be adjusted based on:
    - Number of items found
    - Individual field confidences
    - Arithmetic consistency between items and total
    """
    calculated = []
    for field in items:
        # Use the field's existing confidence and evidence
        evidence = _default_evidence(field) if hasattr(field, 'confidence') else {}
        calc_field = calculate_field_confidence(field, evidence)
        calculated.append(calc_field)

    return calculated


# Export all functions
__all__ = [
    "calculate_field_confidence",
    "calculate_items_confidence",
    "_default_evidence",
]