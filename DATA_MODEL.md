# Data Models — Carbon Crunch Receipt Intelligence

## Primary Models (Pydantic)

### Receipt
```python
class Receipt(BaseModel):
    receipt_id: str
    source_image: str
    store_name: Optional[ExtractedField] = None
    date: Optional[ExtractedField] = None
    items: List[ReceiptItem] = []
    total_amount: Optional[ExtractedField] = None
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    pipeline_status: PipelineStatus = PipelineStatus.COMPLETED
    errors: List[str] = []
```

### OCRResult
```python
class OCRResult(BaseModel):
    text: str
    confidence: float
    bounding_box: List[Tuple[int, int]]
```

### OCRTextLine
```python
class OCRTextLine(BaseModel):
    text: str
    confidence: float
    box: List[Tuple[int, int]]
    line_number: int
```

### ExtractedField
```python
class ExtractedField(BaseModel):
    value: Optional[Any] = None
    confidence: float = 0.0
    status: FieldStatus = FieldStatus.LOW_CONFIDENCE
    
    @property
    def is_high_confidence(self) -> bool:
        return self.status == FieldStatus.HIGH_CONFIDENCE
    
    @property
    def is_medium_confidence(self) -> bool:
        return self.status == FieldStatus.MEDIUM_CONFIDENCE
    
    @property
    def is_low_confidence(self) -> bool:
        return self.status == FieldStatus.LOW_CONFIDENCE
    
    @property
    def is_missing(self) -> bool:
        return self.status == FieldStatus.MISSING
    
    @property
    def is_conflict(self) -> bool:
        return self.status == FieldStatus.CONFLICT
```

### ReceiptItem
```python
class ReceiptItem(BaseModel):
    name: str
    price: str
    confidence: float
    status: FieldStatus = FieldStatus.HIGH_CONFIDENCE
```

### FinancialSummary
```python
class FinancialSummary(BaseModel):
    total_spend: float = 0.0
    number_of_transactions: int = 0
    spend_per_store: Dict[str, float] = {}
```

### EvaluationResult
```python
class EvaluationResult(BaseModel):
    total_receipts: int
    successfully_processed: int
    partially_processed: int
    failed: int
    average_ocr_confidence: float
    average_field_confidence: float
    low_confidence_rate: float
    extraction_metrics: Dict[str, ExtractionMetrics]
```

### PipelineError
```python
class PipelineError(BaseModel):
    receipt_id: str
    error_type: str
    message: str
    stage: str