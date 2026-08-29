# Architecture — Carbon Crunch Receipt Intelligence

```
                         RECEIPT IMAGE
                              │
                              ▼
                    Input Validation
                              │
                              ▼
                    Image Quality Check
                              │
                              ▼
                      Preprocessing
                              │
                              ▼
                          OCR
                              │
                              ▼
                   OCR Normalization
                              │
                              ▼
                  Information Extraction
                    ┌───────┼────────┐
                    ↓       ↓        ↓
                  Store   Date     Items
                                   Prices
                                     │
                                     ▼
                              Total Detection
                                     │
                                     ▼
                                Validation
                                     │
                                     ▼
                            Confidence Engine
                                     │
                                     ▼
                             Conflict Resolver
                                     │
                                     ▼
                              Structured JSON
                                ┌────┴────┐
                                ↓         ↓
                        Financial     Evaluation
                         Summary
```

## Architecture Principles

- **Modular components**: Each stage is an independent, testable module
- **No giant Python file**: Responsibilities are separated across files
- **No fixed receipt coordinates**: All extraction is position-aware but not hardcoded
- **OCR adapter abstraction**: OCR behind an interface for swap-outability
- **Configurable confidence logic**: Weights and thresholds in config.yaml
- **Independent receipt processing**: One receipt's failure doesn't affect others
- **Clear error handling**: Every stage can fail gracefully
- **Testable components**: Units can be tested in isolation
- **Portable paths**: Windows-compatible path handling throughout

## Data Flow

1. **Input Validation** — Check image exists, valid format, readable
2. **Image Quality Assessment** — Evaluate blur, brightness, contrast, skew
3. **Preprocessing** — Apply adaptive transformations based on quality signals
4. **OCR** — Run PaddleOCR, capture text + bounding boxes + confidence
5. **OCR Normalization** — Clean artifacts, handle currency, normalize whitespace
6. **Information Extraction** — Parallel extraction of store, date, items, prices, total
7. **Validation** — Validate dates, currencies, numeric relationships
8. **Confidence Engine** — Combine OCR confidence with pattern, keyword, spatial evidence
9. **Conflict Resolution** — Rank multiple candidates, mark uncertainty
10. **Structured JSON** — Generate per-receipt output
11. **Financial Summary** — Aggregate across successful receipts
12. **Evaluation** — Compute metrics, generate report