"""OCR Base Strategy Interface and unified result schemas."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field


class OCRBoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class OCRLineResult(BaseModel):
    text: str
    confidence: float
    bbox: Optional[OCRBoundingBox] = None


class OCRRawResult(BaseModel):
    engine_name: str
    lines: List[OCRLineResult] = Field(default_factory=list)
    full_text: str = ""
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseOCREngine(ABC):
    """Abstract Base Class for OCR Engines (Strategy Pattern)."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the OCR Engine Strategy."""
        pass

    @abstractmethod
    def extract(
        self, image_np: np.ndarray, metadata: Optional[Dict[str, Any]] = None
    ) -> OCRRawResult:
        """Extract text and bounding boxes from a numpy image matrix.

        Args:
            image_np: Decoded image matrix (BGR or RGB).
            metadata: Optional dictionary with hints.

        Returns:
            OCRRawResult: Normalized raw OCR output.
        """
        pass
