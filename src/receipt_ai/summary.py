# -*- coding: utf-8 -*-
"""Financial summary generation for multiple receipts."""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from .schemas import FinancialSummary, ExtractedField, ReceiptItem


def generate_financial_summary(
    receipts: List[dict],
) -> FinancialSummary:
    """Generate financial summary from list of processed receipts.

    Handles:
    - missing totals
    - invalid totals
    - failed receipts
    - duplicate entries

    One bad receipt must not crash the entire aggregation.
    """
    summary = FinancialSummary()

    for receipt in receipts:
        try:
            # Safely extract total amount
            total_field = receipt.get("total_amount")
            if total_field and isinstance(total_field, dict) and total_field.get("value") is not None:
                try:
                    total_str = str(total_field["value"])
                    # Remove currency symbols and parse
                    clean = re.sub(r'[$€£¥₹]', '', total_str)
                    total_val = float(clean)
                    if total_val > 0:
                        # Extract store name if available
                        store_name = receipt.get("store_name", {})
                        if store_name and isinstance(store_name, dict) and store_name.get("value"):
                            store_val = str(store_name["value"])
                        else:
                            store_val = ""

                        summary.add_transaction(total_val, store_val)
                except (ValueError, TypeError):
                    # Skip invalid total - don't crash
                    continue
            elif total_field is not None:
                # total_field exists but value is None or invalid
                continue
            else:
                # No total_amount field
                continue
        except Exception:
            # Unexpected error - skip this receipt, don't crash
            continue

    return summary


def summarize_receipt(receipt: dict) -> Dict[str, Any]:
    """Create a summary for a single receipt.

    Useful for per-receipt output or debugging.
    """
    items = receipt.get("items", [])

    # Calculate item total
    item_total = 0.0
    for item in items:
        if item.price:
            try:
                clean = re.sub(r'[$€£¥₹]', '', str(item.price))
                item_total += float(clean)
            except ValueError:
                continue

    total_field = receipt.get("total_amount", {})
    total_value = total_field.get("value", "0") if total_field else "0"

    return {
        "receipt_id": receipt.get("receipt_id", "unknown"),
        "store": receipt.get("store_name", {}).get("value", "unknown") if receipt.get("store_name") else "unknown",
        "item_count": len(items),
        "item_total": round(item_total, 2),
        "extracted_total": total_value if total_value else "0",
        "date": receipt.get("date", {}).get("value", "") if receipt.get("date") else "",
        "confidence": receipt.get("total_amount", {}).get("confidence", 0.0),
    }


# Export all functions
__all__ = [
    "generate_financial_summary",
    "summarize_receipt",
]