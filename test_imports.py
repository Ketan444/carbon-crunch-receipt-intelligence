import sys
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')

from receipt_ai.config import PROJECT_ROOT, RAW_DIR, OUTPUT_DIR
print('config OK')

from receipt_ai.schemas import ExtractedField, FieldStatus, ReceiptItem
print('schemas OK')

from receipt_ai.quality import assess_image_quality
print('quality OK')

from receipt_ai.preprocessing import preprocess_image
print('preprocessing OK')

from receipt_ai.ocr import create_ocr_adapter
print('ocr OK')

from receipt_ai.ocr_normalization import normalize_ocr_text, extract_price_from_text
print('ocr_normalization OK')

from receipt_ai.extraction import extract_items, extract_prices_from_text, extract_store_name
print('extraction OK')

from receipt_ai.total_extraction import extract_total
print('total_extraction OK')

from receipt_ai.date_extraction import extract_date
print('date_extraction OK')

from receipt_ai.validation import validate_receipt
print('validation OK')

from receipt_ai.confidence import calculate_field_confidence
print('confidence OK')

from receipt_ai.conflict_resolution import resolve_conflict
print('conflict_resolution OK')

from receipt_ai.summary import generate_financial_summary
print('summary OK')

print('\nALL MODULES IMPORTED SUCCESSFULLY')