import sys, os, json, shutil
sys.path.insert(0, 'src')
from receipt_ai.pipeline import CarbonCrunchPipeline
from receipt_ai.config import RAW_DIR
from pathlib import Path

# Create a temp dir with ONLY 0.jpg
tmp_dir = Path(r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\tmp_single')
if tmp_dir.exists():
    shutil.rmtree(tmp_dir)
tmp_dir.mkdir()

# Copy only 0.jpg
src = Path(RAW_DIR, '0.jpg')
shutil.copy2(src, tmp_dir / '0.jpg')

pipeline = CarbonCrunchPipeline(ocr_engine='paddleocr')

# Process just this one image
result = pipeline.process_receipt(Path(tmp_dir, '0.jpg'))
print(f'Processing result: success={result.success}')

# Now try process_batch with the single-image directory
output_dir = Path(r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\outputs\test')
results = pipeline.process_batch(tmp_dir, output_dir)

print('Batch results:')
print(f'  Total images: {results["total_images"]}')
print(f'  Successfully processed: {results["successfully_processed"]}')
print(f'  Failed: {results["failed"]}')
print(f'  Partially processed: {results["partially_processed"]}')
print(f'  Financial summary total: {results["financial_summary_total"]}')
print(f'  Number of transactions: {results["number_of_transactions"]}')

# Check if JSON was generated
json_path = Path(output_dir / 'receipts' / 'receipt_0.json')
print(f'\\nJSON exists: {json_path.exists()}')
if json_path.exists():
    with open(json_path, 'r') as f:
        data = json.load(f)
    print(f'store_name: {data.get("store_name")}')
    print(f'date: {data.get("date")}')
    print(f'items count: {len(data.get("items", []))}')
    print(f'total_amount: {data.get("total_amount")}')