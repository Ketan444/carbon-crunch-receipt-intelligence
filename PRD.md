# Carbon Crunch — Receipt Document Intelligence Pipeline

## Project Objective

Build a confidence-aware receipt document intelligence system that extracts structured data from receipt images while explicitly representing uncertainty through confidence scores.

## Target Users

- MLOps engineers deploying document intelligence pipelines
- Finance teams automating receipt processing
- Developers building expense tracking applications

## Input

- Receipt image (JPG/PNG formats, varied dimensions, real-world layouts)

## Output

- Structured JSON with extracted fields
- Financial summary across multiple receipts
- Evaluation reports
- Logs of processing

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | Process receipt images from file system |
| FR2 | Preprocess difficult images (noise, blur, skew, rotation, poor lighting) |
| FR3 | Run OCR and capture text, bounding boxes, and OCR confidence |
| FR4 | Extract store name from header region |
| FR5 | Extract transaction date in multiple formats |
| FR6 | Extract items with names and prices |
| FR7 | Extract individual item prices |
| FR8 | Extract total amount |
| FR9 | Calculate field-level confidence for every extracted field |
| FR10 | Flag low-confidence fields |
| FR11 | Resolve ambiguity/conflicts between multiple candidates |
| FR12 | Generate structured JSON output per receipt |
| FR13 | Generate expense summary across receipts |
| FR14 | Generate evaluation report with metrics |
| FR15 | Continue processing when individual receipts fail |
| FR16 | Provide CLI execution |

## Non-Functional Requirements

- Modular architecture with no giant Python files
- No fixed receipt coordinates (configurable)
- OCR adapter abstraction for interchangeability
- Configurable confidence logic
- Independent receipt processing (error isolation)
- Clear error handling (no silent failures)
- Portable paths (Windows-compatible)
- Testable components with unit tests

## Edge Cases

- Noise and blur in images
- Skew and rotation
- Poor lighting and contrast variation
- Different fonts and font sizes
- Unusual receipt layouts
- Partial receipts (cropped edges)
- Missing information (no total, no date)
- Low-quality images
- Multiple date candidates
- Multiple total candidates
- Store name confused with address/phone/tax ID

## Success Criteria

- Extraction accuracy across diverse receipt types
- Confidence scores accurately reflect extraction reliability
- < 5% crash rate on full 371-image dataset
- All extracted fields have confidence scores in [0, 1]
- Low-confidence fields properly flagged
- Conflict resolution produces deterministic results
- CLI works on Windows

## Evaluation Criteria

- Extraction Accuracy (30%)
- Confidence Scoring (20%)
- Robustness (15%)
- Data Structuring (10%)
- Financial Summary (10%)
- Code Quality (10%)
- Edge Cases (5%)

## Future Improvements

- Add support for handwritten receipts
- Integrate with cloud storage
- Add batch processing UI
- Fine-tune OCR on receipt domain
- Add multi-language support