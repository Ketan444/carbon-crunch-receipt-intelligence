# Carbon Crunch — Receipt Document Intelligence

## Overview

**Carbon Crunch** is a confidence-aware receipt document intelligence pipeline that extracts structured data from receipt images while explicitly representing uncertainty through confidence scores.

## Problem Statement

Receipts come in diverse formats, qualities, and layouts. Building a system that reliably extracts store names, dates, items, prices, and totals from these varied inputs — while quantifying the reliability of each extraction — is challenging. OCR quality varies, lighting conditions differ, and receipt designs range from simple to complex multi-column layouts.

## Dataset

The Carbon Crunch dataset contains approximately 371 receipt images in JPG and PNG formats with varied dimensions and real-world receipt layouts. The images include challenges such as:

- Noise and blur
- Skew and rotation
- Poor lighting and contrast variation
- Different fonts and font sizes
- Unusual receipt layouts
- Partial receipts (cropped edges)
- Missing information (no total, no date)
- Low-quality images

## Features

- **Image Quality Assessment**: Evaluates blur, brightness, contrast, and skew to guide preprocessing
- **Adaptive Preprocessing**: Creates preprocessing variants based on quality signals; selects best OCR output
- **PaddleOCR Integration**: Primary OCR engine with adapter abstraction for interchangeability
- **Multi-Variant OCR**: Runs OCR on multiple preprocessing variants for difficult images; uses agreement between variants to boost confidence
- **Store Extraction**: Extracts store name from header region, with exclusion rules to avoid confusing with address/phone/tax ID
- **Date Extraction**: Supports multiple date formats (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY, DD.MM.YYYY) with candidate ranking
- **Item Extraction**: Hybrid method using OCR, regex, line grouping, and spatial relationships
- **Price Extraction**: Supports various representations (45.00, ₹45.00, $45.00, 45,00)
- **Total Extraction**: Prioritizes contextual keywords (TOTAL, GRAND TOTAL, AMOUNT DUE, BALANCE) with arithmetic consistency checking
- **Field-Level Confidence**: Every extracted field has a confidence score in [0, 1]
- **Status Flags**: HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE, MISSING, CONFLICT
- **Conflict Resolution**: When multiple candidates exist, ranks them and marks uncertainty appropriately
- **Financial Summary**: Aggregates totals and spend-per-store across multiple receipts
- **Evaluation Report**: Generates metrics on processing success, confidence distributions, and extraction quality
- **Error Isolation**: One receipt's failure doesn't affect batch processing
- **CLI Execution**: Full pipeline via command-line interface

## Architecture

The pipeline follows a modular stages:

```
Receipt Image
  → Input Validation
  → Image Quality Assessment (blur, brightness, contrast, skew)
  → Preprocessing (adaptive, quality-based variants)
  → OCR (PaddleOCR + normalization)
  → OCR Normalization (whitespace, currency, artifacts)
  → Information Extraction
       ├── Store (header region)
       ├── Date (multiple formats, candidate ranking)
       ├── Items (line grouping + spatial relationships)
       ├── Prices (regex + normalization)
       └── Total (keywords + arithmetic consistency)
  → Validation (dates, currencies, arithmetic)
  → Confidence Engine (weighted combination)
  → Conflict Resolution (ranked candidates)
  → Structured JSON Output
  → Financial Summary
  → Evaluation Report
```

## Pipeline

```bash
# Process all receipts in data/raw/
python scripts/run_pipeline.py --input data/raw --output outputs

# Evaluate existing results
python scripts/evaluate.py --input data/raw

# Process specific receipt
python scripts/run_pipeline.py --input data/raw --receipt-id receipt_001
```

## Tech Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.11+ |
| Image Processing | OpenCV, Pillow |
| Numerical | NumPy |
| OCR | PaddleOCR |
| Data Models | Pydantic |
| Testing | pytest |
| Config | PyYAML |
| CLI | argparse |

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Verify PaddleOCR installation:
   ```bash
   python -c "from paddleocr import PaddleOCR; print('PaddleOCR available')"
   ```
4. Run the pipeline:
   ```bash
   python scripts/run_pipeline.py --input data/raw --output outputs
   ```

## Usage

### Basic Pipeline

Process all receipt images in the input directory:

```bash
python scripts/run_pipeline.py --input data/raw --output outputs
```

This will:
- Process all receipt images found in `data/raw/`
- Generate one JSON file per receipt in `outputs/receipts/`
- Generate `outputs/expense_summary.json` with aggregated totals
- Generate `outputs/evaluation_report.json` with processing metrics

### CLI Options

```
--input DIR          Input directory with receipt images (default: data/raw)
--output DIR         Output directory (default: outputs)
--ocr-engine ENGINE  OCR engine: paddleocr or fallback (default: paddleocr)
--use-gpu            Use GPU for OCR if available
--receipt-id ID      Process a specific receipt by ID
--list-images        List images and exit
```

### Evaluation

```bash
python scripts/evaluate.py --input data/raw
```

This evaluates existing per-receipt JSON files and generates a summary.

## Project Structure

```
Carbon-Crunch-Receipt-Intelligence/
├── data/
│   ├── raw/          <- Receipt images (extract dataset here)
│   ├── processed/    <- Processed images
│   └── samples/      <- Sample images
├── outputs/
│   ├── receipts/     <- Per-receipt JSON outputs
│   ├── expense_summary.json  <- Aggregated financial summary
│   ├── evaluation_report.json  <- Evaluation metrics
│   └── logs/         <- Processing logs
├── src/
│   └── receipt_ai/
│       ├── config.py       <- Configuration constants
│       ├── schemas.py      <- Pydantic data models
│       ├── __init__.py     <- Package init
│       ├── quality.py      <- Image quality assessment
│       ├── preprocessing.py<- Preprocessing pipeline
│       ├── ocr.py          <- OCR adapter abstraction
│       ├── ocr_normalization.py <- Text normalization
│       ├── extraction.py   <- Store, items, price extraction
│       ├── total_extraction.py <- Total amount extraction
│       ├── date_extraction.py <- Date extraction
│       ├── validation.py   <- Data validation
│       ├── confidence.py   <- Confidence engine
│       ├── conflict_resolution.py <- Conflict handling
│       ├── summary.py      <- Financial summary
│       └── pipeline.py     <- Pipeline orchestration
├── scripts/
│   ├── run_pipeline.py   <- CLI for pipeline
│   └── evaluate.py       <- CLI for evaluation
├── tests/
│   ├── test_quality.py
│   ├── test_preprocessing.py
│   ├── test_ocr.py
│   ├── test_extraction.py
│   ├── test_validation.py
│   ├── test_confidence.py
│   ├── test_summary.py
│   └── test_pipeline.py
├── requirements.txt
├── .gitignore
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── .github/
│   └── workflows/
│       └── ci.yml
└── docs/
    └── INTERNSHIP_REPORT.md
```

## Preprocessing

The system uses adaptive preprocessing based on image quality assessment:

- **Blur detected**: Applies denoising and sharpening variants
- **Dark image**: Brightens and enhances contrast
- **Low contrast**: Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
- **Skew detected**: Deskews using Hough Transform
- **Small image**: Resizes to reasonable dimension
- **Multiple variants**: Creates 5+ preprocessing variants for difficult images
- **Agreement-based selection**: Runs OCR on multiple variants; if outputs agree, confidence increases

Variants created:
1. Original image
2. Grayscale version
3. Contrast-enhanced (CLAHE)
4. Denoised + contrast-enhanced
5. Adaptive thresholded
6. Deskewed

## OCR

Primary OCR engine: **PaddleOCR**

Captured information:
- Text content
- Bounding boxes (essential for spatial reasoning)
- OCR confidence scores

The OCR adapter abstracts the engine, allowing swap-out with minimal changes.

Normalization handles:
- Extra spaces and line breaks
- OCR artifacts and noise
- Currency symbol handling
- Malformed punctuation

## Extraction

### Store

Looks in the header region (top 25% of image). Excludes address, phone, fax, tax ID lines.

### Date

Supports: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY, DD.MM.YYYY

When multiple candidates: ranks by position, context, confidence, and format unambiguity.

### Items

Hybrid method: OCR + regex + keywords + bounding boxes + line grouping + spatial relationships + context + validation.

Excluded: TOTAL, SUBTOTAL, TAX, VAT, GST, DISCOUNT, CHANGE, CASH, CARD, AMOUNT DUE, BALANCE.

### Prices

Supports: 45.00, ₹45.00, $45.00, 45,00

Normalizes safely; preserves original representation for diagnostics.

### Total

Prioritizes: TOTAL, GRAND TOTAL, AMOUNT DUE, BALANCE, NET TOTAL

Uses: keyword strength, currency pattern, position, OCR confidence, context, arithmetic consistency.

DO NOT choose: largest number, last number, first number.

## Confidence Scoring

Every extracted field has confidence in [0, 1], combining:

- OCR confidence (50% weight)
- Pattern validation (20% weight)
- Keyword/context evidence (15% weight)
- Spatial evidence (15% weight)

Thresholds:
- >= 0.85: HIGH_CONFIDENCE
- 0.70–0.849: MEDIUM_CONFIDENCE
- < 0.70: LOW_CONFIDENCE

Missing: MISSING
Conflicting: CONFLICT

## Edge Cases Handled

- Noise and blur in images ✓
- Skew and rotation ✓
- Poor lighting and contrast variation ✓
- Different fonts and font sizes ✓
- Unusual receipt layouts ✓
- Partial receipts (cropped edges) ✓
- Missing information (no total, no date) ✓
- Low-quality images ✓
- Multiple date candidates ✓
- Multiple total candidates ✓
- Store name confused with address/phone/tax ID ✓

## Evaluation

Generate evaluation report with metrics:

- Total receipts processed
- Successfully processed count
- Partially processed count
- Failed count
- Average OCR confidence
- Average field confidence
- Low-confidence rate
- Arithmetic consistency rate

## Limitations

- PaddleOCR performance varies on Windows
- Date ambiguity when day ≤ 12 and month ≤ 12 (e.g., 01/02/2026)
- Total extraction relies on contextual keywords; may fall back to arithmetic
- Item extraction may miss items in very dense or distorted layouts
- Handwritten receipts not supported
- Multi-language receipts limited

## Future Improvements

- Fine-tune PaddleOCR on receipt domain
- Add multi-language OCR support
- Add handwritten receipt handling
- Integrate with cloud storage (Google Drive, S3)
- Add web API interface
- Fine-tune confidence weights on dataset
- Add batch processing progress tracking

## Example JSON Output

```json
{
  "receipt_id": "receipt_001",
  "source_image": "receipt_001.jpg",

  "store_name": {
    "value": "Example Store",
    "confidence": 0.94,
    "status": "HIGH_CONFIDENCE"
  },

  "date": {
    "value": "2026-08-28",
    "confidence": 0.91,
    "status": "HIGH_CONFIDENCE"
  },

  "items": [
    {
      "name": "Milk",
      "price": "45.00",
      "confidence": 0.93,
      "status": "HIGH_CONFIDENCE"
    },
    {
      "name": "Bread",
      "price": "30.00",
      "confidence": 0.88,
      "status": "HIGH_CONFIDENCE"
    }
  ],

  "total_amount": {
    "value": "147.15",
    "confidence": 0.96,
    "status": "HIGH_CONFIDENCE"
  }
}
```

## Limitations

- Dataset ZIP not yet extracted and processed
- PaddleOCR Windows compatibility needs verification
- Confidence weights are initial values, not tuned on dataset
- Some edge cases may still cause extraction failures

## Future Improvements

- Fine-tune OCR on receipt domain
- Add multi-language support
- Add handwritten receipt handling
- Web API for integration
- GUI for manual review and correction