#!/usr/bin/env python
"""Evaluate processed receipt results."""

import sys
import json
from pathlib import Path

# Add project source to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.receipt_ai.schemas import EvaluationResult


def load_evaluation_report(path: Optional[Path] = None) -> EvaluationResult:
    """Load evaluation report from file."""
    if path is None:
        path = project_root / "outputs" / "evaluation_report.json"

    data = None
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    if data:
        return EvaluationResult(**data)
    else:
        # Return empty evaluation result
        return EvaluationResult(
            total_receipts=0,
            successfully_processed=0,
            partially_processed=0,
            failed=0,
        )


def evaluate_single_receipt(path: Path) -> dict:
    """Evaluate a single receipt JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic validation
    result = {
        "receipt_id": data.get("receipt_id", "unknown"),
        "has_store": data.get("store_name", {}).get("value") is not None,
        "has_date": data.get("date", {}).get("value") is not None,
        "has_items": len(data.get("items", [])) > 0,
        "has_total": data.get("total_amount", {}).get("value") is not None,
        "store_confidence": data.get("store_name", {}).get("confidence", 0.0),
        "date_confidence": data.get("date", {}).get("confidence", 0.0),
        "total_confidence": data.get("total_amount", {}).get("confidence", 0.0),
        "item_count": len(data.get("items", [])),
    }

    # Check arithmetic consistency if items and total exist
    items = data.get("items", [])
    total_str = data.get("total_amount", {}).get("value")
    if items and total_str:
        try:
            total_val = float(total_str)
            item_sum = sum(
                float(re.sub(r'[$€£¥₹]', '', item.get("price", "0")))
                for item in items
                if item.get("price")
            )
            deviation = abs(item_sum - total_val) / max(item_sum, total_val, 1)
            result["arithmetic_consistent"] = deviation < 0.1
            result["item_sum"] = round(item_sum, 2)
            result["total_value"] = round(total_val, 2)
            result["deviation"] = round(deviation, 4)
        except (ValueError, TypeError):
            result["arithmetic_consistent"] = False
            result["item_sum"] = None
            result["total_value"] = None
            result["deviation"] = None
    else:
        result["arithmetic_consistent"] = None
        result["item_sum"] = None
        result["total_value"] = None
        result["deviation"] = None

    return result


def main():
    """Main entry point for evaluation CLI."""
    parser = argparse.ArgumentParser(
        description="Carbon Crunch: Evaluation Pipeline"
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw"),
        help="Input directory containing receipt images (default: data/raw)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output evaluation report path (default: outputs/evaluation_report.json)",
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output per-receipt evaluation as JSON files",
    )

    args = parser.parse_args()

    # Resolve paths
    project_root = Path(__file__).parent.parent.parent.parent
    input_dir = project_root / args.input if not args.input.is_absolute() else args.input
    output_path = project_root / (args.output or "outputs/evaluation_report.json")

    # Find all image files
    image_files = []
    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        image_files.extend(input_dir.glob(f"*{ext}"))
        image_files.extend(input_dir.glob(f"*{ext.upper()}"))

    print(f"Evaluating {len(image_files)} receipt images...")
    print()

    # Process each image's JSON output (if available)
    # First check if any per-receipt JSON files exist
    receipts_dir = project_root / "outputs" / "receipts"
    json_files = list(receipts_dir.glob("*.json")) if receipts_dir.exists() else []

    evaluation_results = []

    if json_files:
        # Evaluate existing per-receipt JSON files
        print(f"Found {len(json_files)} per-receipt JSON files:")
        for json_file in sorted(json_files):
            eval_result = evaluate_single_receipt(json_file)
            evaluation_results.append(eval_result)
            print(f"  {json_file.name}:")
            print(f"    Store: {'YES' if eval_result['has_store'] else 'NO'}")
            print(f"    Date: {'YES' if eval_result['has_date'] else 'NO'}")
            print(f"    Items: {eval_result['item_count']}")
            print(f"    Total: {'YES' if eval_result['has_total'] else 'NO'}")
            print(f"    Arithmetic consistent: {'YES' if eval_result.get('arithmetic_consistent') else 'N/A'}")

        # Generate summary evaluation
        if evaluation_results:
            total = len(json_files)
            successful = sum(1 for r in evaluation_results if r['has_store'] and r['has_date'] and r['has_total'])
            partially = sum(1 for r in evaluation_results if not (r['has_store'] and r['has_date'] and r['has_total']))
            failed = total - successfully - partially

            avg_item_count = round(sum(r['item_count'] for r in evaluation_results) / len(evaluation_results), 2) if evaluation_results else 0

            # Average confidences
            avg_store_conf = round(sum(r['store_confidence'] for r in evaluation_results) / len(evaluation_results), 4) if evaluation_results else 0
            avg_date_conf = round(sum(r['date_confidence'] for r in evaluation_results) / len(evaluation_results), 4) if evaluation_results else 0
            avg_total_conf = round(sum(r['total_confidence'] for r in evaluation_results) / len(evaluation_results), 4) if evaluation_results else 0

            # Arithmetic consistency rate
            consistent_count = sum(1 for r in evaluation_results if r.get('arithmetic_consistent'))
            consistency_rate = round(consistent_count / len(evaluation_results), 4) if evaluation_results else 0

            # Write evaluation report
            from src.receipt_ai.schemas import EvaluationResult
            eval_report = EvaluationResult(
                total_receipts=total,
                successfully_processed=successfully,
                partially_processed=partially,
                failed=failed,
                average_ocr_confidence=avg_total_conf,  # Using total conf as proxy
                average_field_confidence=round((avg_store_conf + avg_date_conf + avg_total_conf) / 3, 4) if evaluation_results else 0,
                low_confidence_rate=round(
                    sum(1 for r in evaluation_results if r['total_confidence'] < 0.70) / len(evaluation_results), 4
                ) if evaluation_results else 0,
            )

            # Save evaluation report
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(eval_report.to_dict(), f, indent=2)

            print()
            print("Evaluation Summary:")
            print(f"  Total receipts: {total}")
            print(f"  Successfully processed: {successful}")
            print(f"  Partially processed: {partially}")
            print(f"  Failed: {failed}")
            print(f"  Average item count per receipt: {avg_item_count}")
            print(f"  Average field confidence: {eval_report.average_field_confidence}")
            print(f"  Low-confidence rate: {eval_report.low_confidence_rate}")
            print(f"  Arithmetic consistency rate: {consistency_rate}")
            print(f"  Evaluation report saved to: {output_path}")

    else:
        print("No per-receipt JSON files found.")
        print("Run the pipeline first to generate JSON outputs.")
        print(f"Expected location: {receipts_dir}/*.json")


if __name__ == "__main__":
    main()