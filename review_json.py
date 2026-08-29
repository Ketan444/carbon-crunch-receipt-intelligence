import sys, os, json
sys.path.insert(0, 'src')
from receipt_ai.pipeline import CarbonCrunchPipeline
from receipt_ai.config import RAW_DIR
from pathlib import Path

# Check the JSON output for 0.jpg
json_path = Path(r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\outputs\receipts\receipt_0.json')
if json_path.exists():
    with open(json_path, 'r') as f:
        data = json.load(f)
    print('=== 0.jpg JSON OUTPUT ===')
    sn = data.get('store_name')
    if isinstance(sn, dict):
        print(f'store_name: value={sn.get("value")}, confidence={sn.get("confidence")}, status={sn.get("status")}')
    else:
        print(f'store_name: {sn}')
    dt = data.get('date')
    if isinstance(dt, dict):
        print(f'date: value={dt.get("value")}, confidence={dt.get("confidence")}, status={dt.get("status")}')
    else:
        print(f'date: {dt}')
    items = data.get('items', [])
    print(f'items count: {len(items)}')
    for item in items:
        print(f'  item: name={item.get("name")}, price={item.get("price")}, confidence={item.get("confidence")}')
    ta = data.get('total_amount')
    if isinstance(ta, dict):
        print(f'total_amount: value={ta.get("value")}, confidence={ta.get("confidence")}, status={ta.get("status")}')
    else:
        print(f'total_amount: {ta}')
    print(f'ocr_confidence: {data.get("ocr_confidence")}')
else:
    print('JSON not found at', json_path)

# Check outputs directory structure
outputs_dir = Path(r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\outputs')
print('\\n=== Outputs directory ===')
if outputs_dir.exists():
    for f in sorted(outputs_dir.glob('*.json')):
        print(f'  File: {f.name}')