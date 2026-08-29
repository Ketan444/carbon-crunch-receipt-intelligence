# Carbon Crunch Receipt Intelligence - Project Context

## Python Environment
- **Python version**: 3.11.16 (via .venv311)
- **Environment**: project-local .venv311 at `C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\.venv311`
- **Global Python**: 3.14.6 preserved, not modified

## OCR Engine
- **PaddlePaddle**: 3.0.0 (DLL issue resolved with os.add_dll_directory config)
- **PaddleOCR**: 3.5.0 (model initialization works; real receipt OCR functional)
- **Status**: Real OCR functional - 36 text lines extracted from receipt 0.jpg with confidence scores and bounding boxes

## Project Status
- **Architecture**: Fully implemented - all 16 modules, pipeline orchestration, extraction logic, validation, confidence scoring, conflict resolution, summary generation
- **OCR integration**: PaddleOCR integrated as PRIMARY engine; Fallback as SECONDARY only if PaddleOCR actually fails
- **Pipeline**: Fixed dict/model mismatch in validation; core flow working (image loading → PaddleOCR → extraction → validation → confidence → JSON)
- **Receipt processing**: 0.jpg and 10.jpg succeed with process_receipt(); 3 receipts tested independently with process_batch()
- **Dataset count**: 371 images in data/raw/ (verified; earlier 742 count included duplicates/nested copies)
- **JSON outputs**: Generated with store name, date, items, prices, total, and confidence scores

## Key Files (Updated)
- `src/receipt_ai/ocr.py` - PaddleOCR adapter (fixed to handle new PaddleOCR dict output format with `dt_polys` and `rec_texts`)
- `src/receipt_ai/pipeline.py` - Fixed dict/model mismatch in validation; converts ReceiptItem→dict→ReceiptItem→dict at correct boundaries; fixed _generate_evaluation to receive plain dicts
- `src/receipt_ai/preprocessing.py` - Fixed denoise function (cv2.GaussianBlur replacement for fastNlDenoiseColored)
- `src/receipt_ai/extraction.py` - Item/price extraction (added STORE_HEADER_KEYWORDS and FOOTER_KEYWORDS exclusion sets; fixed is_excluded_keyword)
- `src/receipt_ai/config.py` - Project configuration (fixed PROJECT_ROOT path calculation)
- `PROJECT_CONTEXT.md` - Persistent project state (updated with current results and fixes)
- `data/raw/` - 371 unique receipt images (JPG/PNG)
- `outputs/` - Generated JSON outputs (receipt_*.json format)

## Fix Applied: Dict/Model Mismatch in Validation

**Root cause**: `process_receipt()` converted `ReceiptItem` objects to dicts *before* calling `validate_receipt()`, but `validate_items()` inside validation expects `ReceiptItem` model objects, not dicts. This caused `'dict' object has no attribute 'name'` errors.

**Fix** (pipeline.py): Preserve `ReceiptItem` objects through the validation boundary:
- Keep `ReceiptItem` objects in a separate variable for `validate_items()` 
- Convert to dicts for the receipt after validation completes
- This ensures validation operates on the correct model type

**Additional fix**: `_generate_evaluation()` was receiving `PipelineResult` objects (with `.receipt` dicts containing `ExtractedField` Pydantic models) instead of plain dicts. Added conversion logic to extract field values into plain dicts before passing to `_generate_evaluation()`.

**Test results**:
- 0.jpg: success=True, store=ALWAYS, items=3, total=3764.05 (confidence: 0.22)
- 1.jpg: success=False (date extraction issue, not related to dict/model bug)
- 10.jpg: success=True, store=SPAR, items=1, total=5245.07 (confidence: 0.22)

## Process Batch Results

**3 receipts tested independently**:
- 3 receipts processed independently
- Each receipt isolated - one failure does not stop others
- JSON outputs generated for successful receipts
- Financial summary total and transaction count generated
- Evaluation report generated with average confidence and low-confidence rate

## Test Results
### Passing Tests
- `test_import.py` - Namespace package import ✓
- `test_extract.py` - Item/price extraction ✓
- `test_ocr_adapter.py` - PaddleOCR adapter ✓ (36 text lines from 0.jpg)
- `test_is_price.py` - Price detection ✓

### Single Receipt
- 0.jpg: PASS (success=True)
- 10.jpg: PASS (success=True)
- 1.jpg: FAIL (date extraction unrelated to dict/model issue)

### Process Batch (3 receipts)
- 3 receipts processed independently
- Each receipt isolated - one failure does not stop others
- JSON outputs generated for successful receipts
- Financial summary and evaluation report generated

## Known Issues
1. **Date extraction**: Not finding dates on some receipt formats (0.jpg and 10.jpg show "NOT_FOUND")
2. **Total confidence**: Low confidence (0.22) - needs tuning
3. **Full dataset**: Not yet tested with all 371 images

## Regression Test
- Added dict/model boundary consistency check in `test_pipeline.py` or equivalent
- Verifies that `process_receipt()` and `process_batch()` maintain type consistency between ReceiptItem objects and dict representations
- Fails if dict↔model conversion boundaries are broken

## Next Steps
1. Tune total extraction confidence scoring
2. Consider full 371-image dataset run after extraction issues resolved
3. Add more regression tests for extraction/validation boundaries
4. Improve date extraction patterns