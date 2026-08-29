import sys
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence')

from receipt_ai.ocr import PaddleOCRAdapter
from receipt_ai.config import OCR_LANG, OCR_USE_GPU
import numpy as np
import os
import cv2
import json

# Test creating PaddleOCR adapter
adapter = PaddleOCRAdapter(lang=OCR_LANG, use_gpu=OCR_USE_GPU)
print('PaddleOCRAdapter created successfully')

# Test with a sample image from data/raw
raw_dir = r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\data\raw'
images = [f for f in os.listdir(raw_dir) if f.endswith(('.jpg', '.png', '.jpeg'))][:1]
img_name = images[0]
img_path = os.path.join(raw_dir, img_name)
img = cv2.imread(img_path)

# Direct OCR call to see structure
results = adapter.ocr.ocr(img)
print('Number of results:', len(results))
first_result = results[0]
print('First result keys:', list(first_result.keys()))

# Get first text line's bbox
dt_polys = first_result.get('dt_polys', [])
if dt_polys:
    first_bbox = dt_polys[0]
    print('First bbox type:', type(first_bbox))
    print('First bbox:', first_bbox[:2] if len(first_bbox) > 0 else 'empty')
    # Check the structure
    print('First bbox[0]:', first_bbox[0] if len(first_bbox) > 0 else 'N/A')
    
# Also check rec_texts
rec_texts = first_result.get('rec_texts', [])
if rec_texts:
    print('First rec_text:', rec_texts[0])
    
# Print a sample of all texts
print('All rec_texts (first 10):')
for i, t in enumerate(rec_texts[:10]):
    print(f'  {i}: {t}')