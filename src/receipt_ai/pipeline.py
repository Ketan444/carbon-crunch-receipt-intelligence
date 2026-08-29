# -*- coding: utf-8 -*-
"""Pipeline orchestration for receipt processing."""

import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import cv2
import numpy as np

from .config import (
    PROJECT_ROOT, RAW_DIR, OUTPUT_DIR, RECEIPTS_DIR,
    LOGS_DIR, EXPENSE_SUMMARY_PATH, EVALUATION_REPORT_PATH,
    CONFIDENCE_WEIGHTS, CONFIDENCE_THRESHOLDS, FIELD_STATUSES
)
from .schemas import (
    Receipt, ExtractedField, FieldStatus, ReceiptItem,
    FinancialSummary, EvaluationResult, PipelineError
)
from .quality import assess_image_quality, get_preprocessing_recommendations
from .preprocessing import preprocess_image, resize_image
from .ocr import create_ocr_adapter, OCRAdapter
from .ocr_normalization import normalize_ocr_text, extract_date_from_text, extract_price_from_text
from .extraction import extract_store_name, extract_items, extract_prices_from_text
from .total_extraction import extract_total
from .date_extraction import extract_date
from .validation import validate_receipt, validate_items
from .confidence import calculate_field_confidence
from .conflict_resolution import resolve_conflict
from .summary import generate_financial_summary, summarize_receipt

# Set up logging
import os
logger = logging.getLogger("carbon_crunch")
os.makedirs(LOGS_DIR, exist_ok=True)
handler = logging.FileHandler(str(LOGS_DIR / "pipeline.log"))
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class PipelineResult:
    """Result of pipeline processing a single receipt."""

    def __init__(self):
        self.receipt_id: str = ""
        self.success: bool = False
        self.receipt: Optional[dict] = None
        self.errors: List[str] = []
        self.processing_time: float = 0.0


class CarbonCrunchPipeline:
    """Main pipeline orchestration class."""

    def __init__(self, ocr_engine: str = "paddleocr", use_gpu: bool = False):
        self.ocr_adapter: OCRAdapter = create_ocr_adapter(engine=ocr_engine, use_gpu=use_gpu)
        self.ocr_available: bool = self.ocr_adapter.is_available()
        self.results: List[PipelineResult] = []

    def process_receipt(
        self,
        image_path: Path,
        receipt_id: Optional[str] = None,
    ) -> PipelineResult:
        """Process a single receipt image through the full pipeline.

        Args:
            image_path: Path to the receipt image file
            receipt_id: Optional ID; generated from filename if not provided

        Returns:
            PipelineResult with extracted data and any errors
        """
        start_time = time.time()
        result = PipelineResult()
        result.receipt_id = receipt_id or image_path.stem

        try:
            # Step 1: Input validation
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")

            result.errors.append(f"Loaded image: {image_path.name}")

            # Step 2: Image quality assessment
            quality = assess_image_quality(image)
            result.errors.append(f"Quality assessment: blur={quality['blur_status']}, "
                                f"brightness={quality['brightness_status']}, "
                                f"contrast={quality['contrast_status']}")

            # Step 3: Preprocessing
            variant_images = preprocess_image(image, quality)

# Step 4: OCR on original and variants
            ocr_results = []
            # Run OCR on original
            if self.ocr_available:
                original_ocr = self.ocr_adapter.extract_text(image)
                # Convert OCRResultAdapter objects to tuples (text, confidence, bbox) for extraction modules
                original_tuples = [(r.text, r.confidence, r.bounding_box) for r in original_ocr]
                ocr_results.extend(original_tuples)

            # Run OCR on best variant(s) if quality is poor
            if quality["blur_status"] in ("BLURRY", "MODERATELY_BLURRY") and self.ocr_available:
                for var_idx, var_image in enumerate(variant_images[1:], 1):
                    var_ocr = self.ocr_adapter.extract_text(var_image)
                    # Convert OCRResultAdapter objects to tuples and mark variant
                    var_tuples = [(r.text, r.confidence, r.bounding_box, var_idx) for r in var_ocr]
                    ocr_results.extend(var_tuples)

            result.errors.append(f"OCR extracted {len(ocr_results)} text lines")

            if not ocr_results:
                raise ValueError("No OCR text extracted")

            # Step 5: OCR normalization
            full_ocr_text = " ".join(r[0] for r in ocr_results)
            normalized_text = normalize_ocr_text(full_ocr_text)

            # Step 6: Information extraction
            height, width = image.shape[:2]

            # 6a: Extract store name
            store_field = extract_store_name(ocr_results, height, width)
            result.errors.append(f"Store extraction: {store_field.value or 'NOT_FOUND'} "
                                f"(confidence: {store_field.confidence})")

            # 6b: Extract date
            date_candidates = extract_date(normalized_text)
            if date_candidates:
                # Pick best candidate
                best_date = date_candidates[0]  # Already ranked
                date_field = ExtractedField(
                    value=best_date["value"],
                    confidence=best_date.get("confidence", 0.7),
                    status=FieldStatus.HIGH_CONFIDENCE
                    if best_date.get("confidence", 0) >= 0.85
                    else FieldStatus.MEDIUM_CONFIDENCE,
                )
            else:
                date_field = ExtractedField(value=None, confidence=0.0, status=FieldStatus.MISSING)
            result.errors.append(f"Date extraction: {date_field.value or 'NOT_FOUND'}")

            # 6c: Extract items
            items = extract_items(ocr_results, height, width)
            result.errors.append(f"Item extraction: {len(items)} items found")

            # 6d: Extract prices
            all_prices = extract_prices_from_text(normalized_text)

            # 6e: Extract total
            total_field = extract_total(
                normalized_text,
                all_prices,
                ocr_confidence=self._average_ocr_confidence(ocr_results),
            )
            result.errors.append(f"Total extraction: {total_field.value or 'NOT_FOUND'} "
                                f"(confidence: {total_field.confidence})")

            # Step 7: Build receipt object - keep ReceiptItem objects for validation
            items_receipt_items = [
                ReceiptItem(name=item.name, price=item.price, confidence=item.confidence, status=item.status)
                for item in items
            ]
            receipt = {
                "receipt_id": result.receipt_id,
                "source_image": str(image_path),
                "store_name": store_field,
                "date": date_field,
                "items": [
                    {
                        "name": item.name,
                        "price": item.price,
                        "confidence": item.confidence,
                        "status": item.status.value,
                    }
                    for item in items
                ],
                "total_amount": total_field,
                "ocr_text": full_ocr_text,
                "ocr_confidence": self._average_ocr_confidence(ocr_results),
                "pipeline_status": "COMPLETED",
                "errors": [],
            }

            # Step 8: Validation - convert dict items back to ReceiptItem for validate_items
            receipt["items"] = validate_items(items_receipt_items)

            # Convert items back to dicts after validation
            receipt["items"] = [
                {
                    "name": item.name,
                    "price": item.price,
                    "confidence": item.confidence,
                    "status": item.status.value,
                }
                for item in receipt["items"]
            ]

            # Step 9: Confidence recalculation (if needed)
            # Recalculate field confidences using the confidence engine
            date_field = receipt["date"]
            if date_field.value:
                calculate_field_confidence(date_field)

            total_field = receipt["total_amount"]
            calculate_field_confidence(total_field)

            # Step 10: Conflict resolution (if multiple candidates existed)
            # Already handled in extraction modules

            result.receipt = receipt
            result.success = True

            logger.info(f"Successfully processed receipt: {result.receipt_id}")

        except Exception as e:
            logger.error(f"Error processing receipt {result.receipt_id}: {str(e)}")
            result.errors.append(str(e))
            # Don't set result.receipt - failure is isolated
            result.success = False

        finally:
            result.processing_time = time.time() - start_time

        return result

    def process_batch(
        self,
        input_dir: Path,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Process all receipt images in a directory.

        Args:
            input_dir: Directory containing receipt images
            output_dir: Optional directory for JSON output files

        Returns:
            Summary dict with processing statistics
        """
        output_dir = output_dir or RECEIPTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find all image files
        image_files = []
        for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            image_files.extend(input_dir.glob(f"*{ext}"))
            image_files.extend(input_dir.glob(f"*{ext.upper()}"))

        logger.info(f"Found {len(image_files)} images in {input_dir}")

        # Process each image independently
        for image_path in sorted(image_files):
            result = self.process_receipt(image_path)

            # Save per-receipt JSON output
            if result.success and result.receipt:
                receipt_id = result.receipt["receipt_id"]
                output_path = output_dir / f"{receipt_id}.json"

                # Convert ExtractedField objects to dict for JSON serialization
                json_receipt = self._receipt_to_dict(result.receipt)
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(json_receipt, f, indent=2, ensure_ascii=False)
                    logger.info(f"Saved output: {output_path}")
                except Exception as e:
                    logger.error(f"Failed to save output {output_path}: {e}")

            # Track results even on failure (error isolation)
            self.results.append(result)

        # Generate financial summary
        successful_receipts = [r for r in self.results if r.success and r.receipt]
        financial_summary = generate_financial_summary(
            [r.receipt for r in successful_receipts]
        )

        # Convert receipt dicts with ExtractedField objects to plain dicts for _generate_evaluation
        eval_receipts = []
        for receipt in [r.receipt for r in successful_receipts]:
            def _convert_field(f):
                if hasattr(f, 'to_dict'):
                    d = f.to_dict()
                elif isinstance(f, dict):
                    d = f
                else:
                    d = {"value": f.value, "confidence": f.confidence, "status": f.status.value}
                return d

            d = {
                "receipt_id": receipt.get("receipt_id", ""),
                "source_image": receipt.get("source_image", ""),
                "store_name": _convert_field(receipt.get("store_name")),
                "date": _convert_field(receipt.get("date")),
                "items": receipt.get("items", []),
                "total_amount": _convert_field(receipt.get("total_amount")),
                "ocr_text": receipt.get("ocr_text", ""),
                "ocr_confidence": receipt.get("ocr_confidence", 0.0),
                "pipeline_status": receipt.get("pipeline_status", "COMPLETED"),
                "errors": receipt.get("errors", []),
            }
            eval_receipts.append(d)

        # Generate evaluation report
        evaluation = self._generate_evaluation(eval_receipts, len(image_files))

        # Save financial summary
        try:
            with open(str(EXPENSE_SUMMARY_PATH), "w", encoding="utf-8") as f:
                json.dump(financial_summary.to_dict(), f, indent=2)
            logger.info(f"Saved expense summary: {EXPENSE_SUMMARY_PATH}")
        except Exception as e:
            logger.error(f"Failed to save expense summary: {e}")

        # Save evaluation report
        try:
            with open(str(EVALUATION_REPORT_PATH), "w", encoding="utf-8") as f:
                json.dump(evaluation.to_dict(), f, indent=2)
            logger.info(f"Saved evaluation report: {EVALUATION_REPORT_PATH}")
        except Exception as e:
            logger.error(f"Failed to save evaluation report: {e}")

        # Return summary
        return {
            "total_images": len(image_files),
            "successfully_processed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "partially_processed": sum(
                1 for r in self.results
                if r.success and r.errors and any("NOT_FOUND" in e for e in r.errors)
            ),
            "financial_summary_total": financial_summary.total_spend,
            "number_of_transactions": financial_summary.number_of_transactions,
            "evaluation_report_path": str(EVALUATION_REPORT_PATH),
            "expense_summary_path": str(EXPENSE_SUMMARY_PATH),
        }

    def _receipt_to_dict(self, receipt: dict) -> dict:
        """Convert receipt dict to JSON-serializable dict."""
        result = {
            "receipt_id": receipt.get("receipt_id", ""),
            "source_image": receipt.get("source_image", ""),
            "ocr_text": receipt.get("ocr_text", ""),
            "ocr_confidence": receipt.get("ocr_confidence", 0.0),
            "pipeline_status": receipt.get("pipeline_status", "COMPLETED"),
            "errors": receipt.get("errors", []),
        }

        # Store name
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

        # Items
        items = receipt.get("items", [])
        result["items"] = []
        for item in items:
            if isinstance(item, dict):
                result["items"].append({
                    "name": item.get("name", ""),
                    "price": item.get("price", "0.00"),
                    "confidence": item.get("confidence", 0.0),
                    "status": item.get("status", "HIGH_CONFIDENCE"),
                })
            elif hasattr(item, "name"):
                result["items"].append({
                    "name": item.name,
                    "price": item.price,
                    "confidence": item.confidence,
                    "status": item.status.value if hasattr(item, "status") else "HIGH_CONFIDENCE",
                })

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
        }

        return result

    def _average_ocr_confidence(self, ocr_results: List) -> float:
        """Calculate average OCR confidence from results."""
        if not ocr_results:
            return 0.0
        # ocr_results are now tuples (text, confidence, bbox) or OCRResultAdapter objects
        confidences = []
        for r in ocr_results:
            if isinstance(r, tuple):
                # Tuple format: (text, confidence, bbox)
                if len(r) > 1:
                    confidences.append(r[1])
            elif hasattr(r, "confidence"):
                confidences.append(r.confidence)
        if confidences:
            return round(sum(confidences) / len(confidences), 4)
        return 0.0

    def _generate_evaluation(
        self,
        successful: List[dict],
        total_count: int,
    ) -> EvaluationResult:
        """Generate evaluation report metrics."""
        if total_count == 0:
            return EvaluationResult(
                total_receipts=0,
                successfully_processed=0,
                partially_processed=0,
                failed=0,
            )

        avg_ocr = 0.0
        avg_field = 0.0
        low_confidence_count = 0

        # Calculate average OCR confidence
        ocr_confidences = []
        for r in successful:
            ocr_conf = r.get("ocr_confidence", 0)
            ocr_confidences.append(ocr_conf)

        if ocr_confidences:
            avg_ocr = round(sum(ocr_confidences) / len(ocr_confidences), 4)

        # Calculate average field confidence and low-confidence rate
        all_fields = []
        for r in successful:
            # Collect all fields
            for field_key in ["store_name", "date"]:
                field = r.get(field_key, {})
                if field and isinstance(field, dict):
                    all_fields.append({
                        "confidence": field.get("confidence", 0.0),
                        "status": field.get("status", "LOW_CONFIDENCE"),
                    })

            # Items
            for item in r.get("items", []):
                if isinstance(item, dict):
                    all_fields.append({
                        "confidence": item.get("confidence", 0.0),
                        "status": item.get("status", "HIGH_CONFIDENCE"),
                    })

            # Total
            total = r.get("total_amount", {})
            if total and isinstance(total, dict):
                all_fields.append({
                    "confidence": total.get("confidence", 0.0),
                    "status": total.get("status", "LOW_CONFIDENCE"),
                })

        if all_fields:
            avg_field = round(sum(f["confidence"] for f in all_fields) / len(all_fields), 4)
            low_confidence_count = sum(
                1 for f in all_fields
                if f["confidence"] < 0.70
            )

        low_confidence_rate = round(low_confidence_count / len(all_fields), 4) if all_fields else 0.0

        partially = sum(
            1 for r in successful
            if r.get("date", {}).get("value") is None
            or r.get("total_amount", {}).get("value") is None
        )

        return EvaluationResult(
            total_receipts=total_count,
            successfully_processed=len(successful),
            partially_processed=partially,
            failed=total_count - len(successful),
            average_ocr_confidence=avg_ocr,
            average_field_confidence=avg_field,
            low_confidence_rate=low_confidence_rate,
        )


# Export the pipeline class
__all__ = [
    "CarbonCrunchPipeline",
    "PipelineResult",
    "process_receipt",
    "process_batch",
]