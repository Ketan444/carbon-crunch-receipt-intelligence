import sys
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')
from receipt_ai.ocr import PaddleOCRAdapter
from receipt_ai.config import OCR_LANG, OCR_USE_GPU
from receipt_ai.extraction import extract_items, _is_price, _group_ocr_into_lines
from receipt_ai.preprocessing import preprocess_image
import cv2
import os

# Test creating PaddleOCR adapter
adapter = PaddleOCRAdapter(lang=OCR_LANG, use_gpu=OCR_USE_GPU)

# Test with receipt 0.jpg
raw_dir = r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\data\raw'
img_path = os.path.join(raw_dir, '0.jpg')
img = cv2.imread(img_path)

# Get OCR results
results = adapter.extract_text(img)
print('OCR text lines:')
for r in results[:10]:
    print(f'  Text: "{r.text}", Conf: {r.confidence:.2f}')

# Convert to tuples for extraction
ocr_tuples = [(r.text, r.confidence, r.bounding_box) for r in results]
print()
print('Grouping into lines:')
lines = _group_ocr_into_lines(ocr_tuples, img.shape[1])
for i, line in enumerate(lines[:5]):
    line_texts = ' '.join(t[0] for t in line)
    print(f'  Line {i}: "{line_texts}" ({len(line)} items)')