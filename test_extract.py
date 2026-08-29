import sys
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')

from receipt_ai.extraction import extract_store_name, extract_items, extract_prices_from_text
from receipt_ai.date_extraction import extract_date
from receipt_ai.total_extraction import extract_total
from receipt_ai.ocr_normalization import normalize_ocr_text
from receipt_ai.schemas import ExtractedField, FieldStatus

# Test with sample OCR text from a receipt
sample_ocr_text = "WALMART SUPERCENTER 123 MAIN ST ANytown ST 01/15/2024 Items: Apple 0.99 Banana 0.59 Milk 2.99 Total $4.57"

normalized = normalize_ocr_text(sample_ocr_text)
print(f"Normalized text: {normalized}")

# Test store name extraction
store = extract_store_name([], 0, 0)  # empty results, should return None
print(f"Store: {store.value if store else 'None'}, confidence: {store.confidence}, status: {store.status}")

# Test date extraction
date_candidates = extract_date(normalized)
print(f"Date candidates: {date_candidates}")
if date_candidates:
    best_date = date_candidates[0]
    date_field = ExtractedField(
        value=best_date["value"],
        confidence=best_date.get("confidence", 0.7),
        status=FieldStatus.HIGH_CONFIDENCE
        if best_date.get("confidence", 0) >= 0.85
        else FieldStatus.MEDIUM_CONFIDENCE,
    )
    print(f"Date: {date_field.value}, confidence: {date_field.confidence}, status: {date_field.status}")

# Test price extraction
prices = extract_prices_from_text(normalized)
print(f"Prices: {prices}")

# Test total extraction
total = extract_total(normalized, prices, ocr_confidence=0.8)
print(f"Total: {total.value if total else 'None'}, confidence: {total.confidence if total else 'N/A'}, status: {total.status if total else 'N/A'}")