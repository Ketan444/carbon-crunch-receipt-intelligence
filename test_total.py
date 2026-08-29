import sys, os
sys.path.insert(0, 'src')
from receipt_ai.pipeline import CarbonCrunchPipeline
from receipt_ai.config import RAW_DIR
from pathlib import Path
import shutil, json

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

# Check the type of total_amount
if result.receipt and result.receipt.get('total_amount'):
    total = result.receipt['total_amount']
    print(f'total_amount type: {type(total)}')
    print(f'has to_dict: {hasattr(total, "to_dict")}')
    if hasattr(total, 'to_dict'):
        print(f'to_dict: {total.to_dict()}')
    print(f'value attr: {total.value if hasattr(total, "value") else "N/A"}')
    print(f'confidence attr: {total.confidence if hasattr(total, "confidence") else "N/A"}')
    print(f'status attr: {total.status if hasattr(total, "status") else "N/A"}')
    
    # Now try _receipt_to_dict
    json_receipt = pipeline._receipt_to_dict(result.receipt)
    print(f'\\n_json_receipt total_amount: {json_receipt.get("total_amount")}')
    # Try to dump
    try:
        json_str = json.dumps(json_receipt, indent=2, ensure_ascii=False)
        print(f'\\nJSON dump successful')
        print(json_str)
    except TypeError as e:
        print(f'\\nJSON dump failed: {e}')
else:
    print('No receipt or total_amount')