# -*- coding: utf-8 -*-
"""OCR adapter abstraction for Carbon Crunch."""

import abc
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import numpy as np

# Try to import PaddleOCR, fall back gracefully
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    PaddleOCR = None


class OCRResultAdapter:
    """Normalized OCR result from any OCR engine."""

    def __init__(
        self,
        text: str,
        confidence: float,
        bounding_box: List[Tuple[int, int]],
    ):
        self.text = text
        self.confidence = confidence
        self.bounding_box = bounding_box


class OCRAdapter(abc.ABC):
    """Abstract base class for OCR adapters."""

    @abc.abstractmethod
    def extract_text(self, image: np.ndarray) -> List[OCRResultAdapter]:
        """Extract text from an image.

        Returns list of OCRResultAdapter with text, confidence, and bounding box.
        """
        pass

    @abc.abstractmethod
    def extract_text_with_boxes(
        self, image: np.ndarray
    ) -> List[Tuple[str, float, List[Tuple[int, int]]]]:
        """Extract text with bounding boxes.

        Returns list of (text, confidence, bounding_box) tuples.
        """
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if the OCR engine is available."""
        pass


class PaddleOCRAdapter(OCRAdapter):
    """PaddleOCR adapter implementation."""

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        if not PADDLEOCR_AVAILABLE:
            raise ImportError(
                "PaddleOCR is not installed. "
                "Install with: pip install paddleocr"
            )
        self.lang = lang
        self.use_gpu = use_gpu
        self.ocr = PaddleOCR(
            lang=lang,
            use_textline_orientation=not use_gpu,
            **({"use_gpu": use_gpu} if use_gpu else {})
        )

    def extract_text(self, image: np.ndarray) -> List[OCRResultAdapter]:
        """Extract text from image using PaddleOCR."""
        if image is None or image.size == 0:
            return []

        # PaddleOCR returns a dict with dt_polys, rec_texts, rec_scores, etc.
        results = self.ocr.ocr(image)

        ocr_results = []
        if results and len(results) > 0 and results[0]:
            result = results[0]  # First (and only) page result
            dt_polys = result.get('dt_polys', [])
            rec_texts = result.get('rec_texts', [])
            rec_scores = result.get('rec_scores', [])

            # Iterate over all detected text lines
            num_lines = max(len(dt_polys), len(rec_texts), len(rec_scores))
            for i in range(num_lines):
                # Get bounding box - dt_polys[i] is a numpy array of 4 points
                if i < len(dt_polys) and dt_polys[i] is not None:
                    bbox_np = dt_polys[i]
                    # bbox_np has shape (4, 2) with [x, y] coordinates
                    bbox_tuples = [
                        (int(point[0]), int(point[1])) for point in bbox_np
                    ]
                else:
                    bbox_tuples = []

                # Get text and confidence
                text = rec_texts[i] if i < len(rec_texts) else ""
                confidence = rec_scores[i] if i < len(rec_scores) else 1.0

                ocr_results.append(OCRResultAdapter(
                    text=text,
                    confidence=float(confidence),
                    bounding_box=bbox_tuples,
                ))

        return ocr_results

    def extract_text_with_boxes(
        self, image: np.ndarray
    ) -> List[Tuple[str, float, List[Tuple[int, int]]]]:
        """Extract text with bounding boxes from image."""
        results = self.extract_text(image)
        return [
            (r.text, r.confidence, r.bounding_box) for r in results
        ]

    def is_available(self) -> bool:
        """Check if PaddleOCR is available."""
        return True  # If class instantiated, it's available


class FallbackOCRAdapter(OCRAdapter):
    """Fallback OCR adapter using minimal processing."""

    def extract_text(self, image: np.ndarray) -> List[OCRResultAdapter]:
        """Return empty list - no real OCR."""
        return []

    def extract_text_with_boxes(
        self, image: np.ndarray
    ) -> List[Tuple[str, float, List[Tuple[int, int]]]]:
        """Return empty list."""
        return []

    def is_available(self) -> bool:
        """Fallback is always available but provides no OCR."""
        return True


def create_ocr_adapter(engine: str = "paddleocr", **kwargs) -> OCRAdapter:
    """Factory function to create OCR adapter."""
    if engine == "paddleocr":
        return PaddleOCRAdapter(**kwargs)
    elif engine == "fallback":
        return FallbackOCRAdapter()
    else:
        raise ValueError(f"Unknown OCR engine: {engine}")