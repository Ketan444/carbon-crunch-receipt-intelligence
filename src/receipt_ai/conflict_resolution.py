# -*- coding: utf-8 -*-
"""Conflict resolution for multiple extraction candidates."""

from typing import List, Dict, Any, Optional, Tuple
from .schemas import ExtractedField, FieldStatus


def resolve_conflict(
    candidates: List[Tuple[ExtractedField, str]],
    strategy: str = "ranked",
) -> ExtractedField:
    """Resolve conflict between multiple extraction candidates.

    When multiple candidates exist (e.g., multiple total candidates,
    multiple date candidates), rank them and return the best one
    with appropriate confidence/status.

    Args:
        candidates: List of (ExtractedField, reason) tuples
        strategy: Resolution strategy ("ranked", "weighted", "consensus")

    Returns:
        Single ExtractedField with the resolved value
    """
    if not candidates:
        return ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)

    if len(candidates) == 1:
        field, reason = candidates[0]
        # Still adjust status based on confidence
        if field.confidence >= 0.85:
            field.status = FieldStatus.HIGH_CONFIDENCE
        elif field.confidence >= 0.70:
            field.status = FieldStatus.MEDIUM_CONFIDENCE
        else:
            field.status = FieldStatus.LOW_CONFIDENCE
        return field

    # Rank candidates using available evidence
    ranked = _rank_candidates(candidates, strategy)

    # Return the best candidate
    best_field, best_reason = ranked[0]

    # Adjust status based on confidence gap and ambiguity
    best_confidence = best_field.confidence

    # If the gap between top and second is small, mark as LOW_CONFIDENCE
    if len(ranked) > 1:
        second_confidence = ranked[1][0].confidence
        confidence_gap = best_confidence - second_confidence

        # If gap is small (< 0.1), downgrade confidence
        if confidence_gap < 0.1:
            best_field.status = FieldStatus.LOW_CONFIDENCE
            best_field.confidence = round(min(best_confidence, 0.7), 4)
        elif confidence_gap < 0.2:
            # Moderate gap - keep MEDIUM unless already high
            if best_field.status != FieldStatus.HIGH_CONFIDENCE:
                best_field.status = FieldStatus.MEDIUM_CONFIDENCE

    # If only one strong candidate but others exist, mark as CONFLICT if ambiguity remains
    if len(ranked) > 2:
        # Multiple candidates with similar strength - CONFLICT
        best_field.status = FieldStatus.CONFLICT
        best_field.confidence = round(min(best_confidence, 0.6), 4)

    # Final status adjustment
    if best_field.confidence >= 0.85:
        best_field.status = FieldStatus.HIGH_CONFIDENCE
    elif best_field.confidence >= 0.70:
        best_field.status = FieldStatus.MEDIUM_CONFIDENCE
    else:
        best_field.status = FieldStatus.LOW_CONFIDENCE

    return best_field


def _rank_candidates(
    candidates: List[Tuple[ExtractedField, str]],
    strategy: str,
) -> List[Tuple[ExtractedField, str]]:
    """Rank candidates using the specified strategy.

    Returns list of (ExtractedField, reason) sorted by priority.
    """
    if strategy == "ranked":
        return _rank_by_evidence(candidates)
    elif strategy == "weighted":
        return _rank_by_weighted_score(candidates)
    elif strategy == "consensus":
        return _rank_by_consensus(candidates)
    else:
        return _rank_by_evidence(candidates)


def _rank_by_evidence(
    candidates: List[Tuple[ExtractedField, str]],
) -> List[Tuple[ExtractedField, str]]:
    """Rank candidates by their confidence evidence.

    Sorts descending by confidence score.
    """
    ranked = sorted(candidates, key=lambda x: x[0].confidence, reverse=True)
    return ranked


def _rank_by_weighted_score(
    candidates: List[Tuple[ExtractedField, str]],
) -> List[Tuple[ExtractedField, str]]:
    """Rank candidates by weighted score combining multiple factors."""
    scored = []
    for field, reason in candidates:
        # Simple weighted score based on confidence and reason
        reason_bonus = 0.0
        if "total" in reason.lower():
            reason_bonus = 0.1
        elif "date" in reason.lower():
            reason_bonus = 0.05

        scored_score = field.confidence + reason_bonus
        scored.append((field, reason, scored_score))

    scored.sort(key=lambda x: x[2], reverse=True)
    return [(s[0], s[1]) for s in scored]


def _rank_by_consensus(
    candidates: List[Tuple[ExtractedField, str]],
) -> List[Tuple[ExtractedField, str]]:
    """Rank candidates by consensus among extraction methods.

    Returns candidates that appear in multiple methods.
    """
    # Group by field value
    value_groups: Dict[str, List[Tuple[ExtractedField, str]]] = {}
    for field, reason in candidates:
        val = field.value or ""
        if val not in value_groups:
            value_groups[val] = []
        value_groups[val].append((field, reason))

    # Return groups with multiple supporters, sorted by confidence
    consensus_groups = []
    for val, group in value_groups.items():
        if len(group) > 1:
            # Sort by confidence within group
            group_sorted = sorted(group, key=lambda x: x[0].confidence, reverse=True)
            consensus_groups.append((group_sorted[0], f"consensus_{val}"))

    # Also include highest-confidence singleton
    if candidates:
        best = max(candidates, key=lambda x: x[0].confidence)
        # Check if this best is already in consensus
        best_val = best[0].value or ""
        in_consensus = any(
            g[0].value == best_val for g in consensus_groups
        )
        if not in_consensus:
            consensus_groups.append(best)

    consensus_groups.sort(key=lambda x: x[0][0].confidence, reverse=True)
    return consensus_groups


# Export all functions
__all__ = [
    "resolve_conflict",
    "_rank_candidates",
    "_rank_by_evidence",
    "_rank_by_weighted_score",
    "_rank_by_consensus",
]