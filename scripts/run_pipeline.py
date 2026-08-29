#!/usr/bin/env python
"""Run the Carbon Crunch receipt processing pipeline."""

import sys
import os
from pathlib import Path

# Project root directory
project_root = Path(r"C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence")

# Add src to path so we can import modules
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import the pipeline module
from receipt_ai.pipeline import CarbonCrunchPipeline


def main():
    """Main entry point for pipeline CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Carbon Crunch: Receipt Document Intelligence Pipeline"
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
        default=Path("outputs"),
        help="Output directory for JSON files and summaries (default: outputs)",
    )

    parser.add_argument(
        "--ocr-engine",
        type=str,
        choices=["paddleocr", "fallback"],
        default="fallback",
        help="OCR engine to use (default: fallback)",
    )

    parser.add_argument(
        "--use-gpu",
        action="store_true",
        default=False,
        help="Use GPU for OCR if available",
    )

    parser.add_argument(
        "--receipt-id",
        type=str,
        default=None,
        help="Process a specific receipt ID (filename stem)",
    )

    parser.add_argument(
        "--list-images",
        action="store_true",
        help="List all images in input directory and exit",
    )

    args = parser.parse_args()

    # Resolve input/output paths
    input_dir = project_root / args.input if not args.input.is_absolute() else args.input
    output_dir = project_root / args.output if not args.output.is_absolute() else args.output

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "receipts").mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir(parents=True, exist_ok=True)

    # Initialize pipeline
    print(f"Initializing Carbon Crunch Pipeline...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"OCR engine: {args.ocr_engine}")
    print(f"Use GPU: {args.use_gpu}")
    print()

    pipeline = CarbonCrunchPipeline(
        ocr_engine=args.ocr_engine,
        use_gpu=args.use_gpu,
    )

    # List images if requested
    if args.list_images:
        image_files = []
        for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            image_files.extend(input_dir.glob(f"*{ext}"))
            image_files.extend(input_dir.glob(f"*{ext.upper()}"))
        print(f"Found {len(image_files)} images in {input_dir}:")
        for f in sorted(image_files):
            print(f"  - {f.name}")
        return

    # Process receipts
    print("-" * 60)
    results = pipeline.process_batch(input_dir, output_dir)
    print("-" * 60)
    print("Pipeline Summary:")
    print(f"  Total images: {results['total_images']}")
    print(f"  Successfully processed: {results['successfully_processed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Partially processed: {results['partially_processed']}")
    print(f"  Financial summary total: ${results['financial_summary_total']:.2f}")
    print(f"  Number of transactions: {results['number_of_transactions']}")
    print()
    print(f"  Receipt JSON files saved to: {results['expense_summary_path']}")
    print(f"  Evaluation report saved to: {results['evaluation_report_path']}")


if __name__ == "__main__":
    main()