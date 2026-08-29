import sys
import os

# Add src to path
src_dir = r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src'
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Add project root to path
proj_dir = r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence'
if proj_dir not in sys.path:
    sys.path.insert(0, proj_dir)

from receipt_ai.ocr import PaddleOCRAdapter, FallbackOCRAdapter, create_ocr_adapter
from receipt_ai.config import OCR_LANG, OCR_USE_GPU
import numpy as np

# Test creating PaddleOCR adapter
adapter = PaddleOCRAdapter(lang=OCR_LANG, use_gpu=OCR_USE_GPU)
print('PaddleOCRAdapter created successfully')

# Test with a sample image from data/raw
raw_dir = r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\data\raw'
images = [f for f in os.listdir(raw_dir) if f.endswith(('.jpg', '.png', '.jpeg'))][:1]
print(f'Testing on: {images[0]}')

img_path = os.path.join(raw_dir, images[0])
from receipt_ai.preprocessing import preprocess_image
import cv2

img = cv2.imread(img_path)
if img is not None:
    processed = preprocess_image(img)
    # extract_text expects a single np.ndarray; preprocess_image returns List[np.ndarray]
    results = adapter.extract_text(processed[0])
    print(f'Number of text lines: {len(results)}')
    for r in results[:5]:
        print(f'  Text: {r.text}, Confidence: {r.confidence:.2f}, BBox: {r.bounding_box[:3]}...')
else:
    print('Failed to load image')