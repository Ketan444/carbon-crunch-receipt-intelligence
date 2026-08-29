#!/usr/bin/env python
import sys
with open('src/receipt_ai/pipeline.py', 'r') as f:
    content = f.read()

old = """# Store name
        store = receipt.get("store_name")
        if store and isinstance(store, dict):
            result["store_name"] = {
                "value": store.get("value"),
                "confidence": store.get("confidence", 0.0),
                "status": store.get("status", "LOW_CONFIDENCE"),
            }
        else:
            result["store_name"] = {
                "value": store,
                "confidence": 0.0,
                "status": "MISSING",
            }

        # Date
        date = receipt.get("date")
        if date and isinstance(date, dict):
            result["date"] = {
                "value": date.get("value"),
                "confidence": date.get("confidence", 0.0),
                "status": date.get("status", "LOW_CONFIDENCE"),
            }
        else:
            result["date"] = {
                "value": date,
                "confidence": 0.0,
                "status": "MISSING",
            }

        # Total amount
        total = receipt.get("total_amount")
        if total and isinstance(total, dict):
            result["total_amount"] = {
                "value": total.get("value"),
                "confidence": total.get("confidence", 0.0),
                "status": total.get("status", "LOW_CONFIDENCE"),
            }
        else:
            result["total_amount"] = {
                "value": total,
                "confidence": 0.0,
                "status": "MISSING",
            }"""

new = """# Store name
        store = receipt.get("store_name")
        if isinstance(store, ExtractedField):
            s = store.to_dict()
        elif store and isinstance(store, dict):
            s = store
        else:
            s = {"value": store, "confidence": 0.0, "status": "MISSING"}
        result["store_name"] = {
            "value": s.get("value"),
            "confidence": s.get("confidence", 0.0),
            "status": s.get("status", "LOW_CONFIDENCE"),
        }

        # Date
        date = receipt.get("date")
        if isinstance(date, ExtractedField):
            d = date.to_dict()
        elif date and isinstance(date, dict):
            d = date
        else:
            d = {"value": date, "confidence": 0.0, "status": "MISSING"}
        result["date"] = {
            "value": d.get("value"),
            "confidence": d.get("confidence", 0.0),
            "status": d.get("status", "LOW_CONFIDENCE"),
        }

        # Total amount
        total = receipt.get("total_amount")
        if isinstance(total, ExtractedField):
            t = total.to_dict()
        elif total and isinstance(total, dict):
            t = total
        else:
            t = {"value": total, "confidence": 0.0, "status": "MISSING"}
        result["total_amount"] = {
            "value": t.get("value"),
            "confidence": t.get("confidence", 0.0),
            "status": t.get("status", "LOW_CONFIDENCE"),
        }"""

if old in content:
    content = content.replace(old, new)
    with open('src/receipt_ai/pipeline.py', 'w') as f:
        f.write(content)
    print('Replacement successful')
else:
    print('Old string not found')
    # Debug: find the Store name line
    idx = content.find('# Store name')
    if idx >= 0:
        print('Found at index', idx)
        print(content[idx:idx+600])
PYEOF