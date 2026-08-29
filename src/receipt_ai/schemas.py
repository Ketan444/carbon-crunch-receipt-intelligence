# -*- coding: utf-8 -*-
"""Pydantic schemas for Carbon Crunch Receipt Intelligence."""

from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, validator
from pathlib import Path
from enum import Enum


class FieldStatus(str, Enum):
    """Status of an extracted field."""
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"


class ExtractedField(BaseModel):
    """A field extracted from a receipt with confidence and status."""
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "confidence": self.confidence,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedField":
        status = FieldStatus(data.get("status", "LOW_CONFIDENCE"))
        return cls(
            value=data.get("value"),
            confidence=data.get("confidence", 0.0),
            status=status,
        )


class ReceiptItem(BaseModel):
    """An item extracted from a receipt."""
    name: str = ""
    price: str = "0.00"
    confidence: float = 0.0
    status: FieldStatus = FieldStatus.HIGH_CONFIDENCE

    def is_high_confidence(self) -> bool:
        return self.status == FieldStatus.HIGH_CONFIDENCE

    def is_low_confidence(self) -> bool:
        return self.status == FieldStatus.LOW_CONFIDENCE


class Receipt(BaseModel):
    """Complete receipt data model."""
    receipt_id: str = ""
    source_image: str = ""
    store_name: Optional[ExtractedField] = None
    date: Optional[ExtractedField] = None
    items: List[ReceiptItem] = Field(default_factory=list)
    total_amount: Optional[ExtractedField] = None
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    pipeline_status: str = "COMPLETED"
    errors: List[str] = Field(default_factory=list)

    model_config = {"protected_namespaces": ()}


class PipelineError(BaseModel):
    """Error information from pipeline processing."""
    receipt_id: str
    error_type: str
    message: str
    stage: str

    model_config = {"protected_namespaces": ()}


class FinancialSummary(BaseModel):
    """Aggregated financial summary across receipts."""
    total_spend: float = 0.0
    number_of_transactions: int = 0
    spend_per_store: Dict[str, float] = Field(default_factory=dict)

    def add_transaction(self, amount: float, store: str = "") -> None:
        """Add a transaction to the summary."""
        self.total_spend += amount
        self.number_of_transactions += 1
        if store:
            if store in self.spend_per_store:
                self.spend_per_store[store] += amount
            else:
                self.spend_per_store[store] = amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_spend": self.total_spend,
            "number_of_transactions": self.number_of_transactions,
            "spend_per_store": {k: round(v, 2) for k, v in self.spend_per_store.items()},
        }


class EvaluationResult(BaseModel):
    """Evaluation metrics for the pipeline."""
    total_receipts: int
    successfully_processed: int
    partially_processed: int
    failed: int
    average_ocr_confidence: float = 0.0
    average_field_confidence: float = 0.0
    low_confidence_rate: float = 0.0
    extraction_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_receipts": self.total_receipts,
            "successfully_processed": self.successfully_processed,
            "partially_processed": self.partially_processed,
            "failed": self.failed,
            "average_ocr_confidence": round(self.average_ocr_confidence, 4),
            "average_field_confidence": round(self.average_field_confidence, 4),
            "low_confidence_rate": round(self.low_confidence_rate, 4),
            "extraction_metrics": self.extraction_metrics,
        }