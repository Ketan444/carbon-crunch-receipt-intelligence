import sys
import os

sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')

from receipt_ai.pipeline import CarbonCrunchPipeline
from receipt_ai.config import RAW_DIR

# Initialize pipeline
pipeline = CarbonCrunchPipeline()

# Get a few sample images
images = [f for f in os.listdir(RAW_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))][:3]
print(f'Testing on {len(images)} images: {images}')

for img_name in images:
    img_path = os.path.join(RAW_DIR, img_name)
    print(f'\nProcessing: {img_name}')
    try:
        result = pipeline.process(img_path)
        print(f'  Store: {result.get("store_name", "N/A")}')
        print(f'  Date: {result.get("date", "N/A")}')
        print(f'  Total: {result.get("total", "N/A")}')
        print(f'  Items count: {len(result.get("items", []))}')
        print(f'  Status: {result.get("status", "N/A")}')
    except Exception as e:
        print(f'  Error: {type(e).__name__}: {str(e)[:100]}')