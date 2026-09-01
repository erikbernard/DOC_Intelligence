"""EasyOCR Strategy Adapter implementing BaseOCREngine."""

import time
from typing import Any, Dict, List, Optional
import numpy as np

from app.core.logging import app_logger
from app.services.ocr.base import (
    BaseOCREngine,
    OCRBoundingBox,
    OCRLineResult,
    OCRRawResult,
)
from app.services.ocr.preprocessor import auto_deskew_and_crop, enhance_contrast


class EasyOCREngineAdapter(BaseOCREngine):
    """EasyOCR implementation adapting the PyTorch CRAFT/CRNN engine."""

    def __init__(self, languages: Optional[List[str]] = None, use_gpu: bool = False) -> None:
        self.languages = languages or ["pt", "en"]
        self.use_gpu = use_gpu
        self._reader = None

    @property
    def engine_name(self) -> str:
        return "EasyOCR_v1"

    def _get_reader(self):
        """Lazy loader for EasyOCR reader to avoid startup overhead."""
        if self._reader is None:
            import easyocr

            app_logger.info(f"Initializing EasyOCR reader with languages={self.languages}, gpu={self.use_gpu}")
            self._reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
        return self._reader

    def extract(
        self, image_np: np.ndarray, metadata: Optional[Dict[str, Any]] = None
    ) -> OCRRawResult:
        """Process image with OpenCV deskew/contrast and perform EasyOCR extraction."""
        start_time = time.time()

        # Step 1: Preprocess with OpenCV
        processed_img = auto_deskew_and_crop(image_np)
        processed_img = enhance_contrast(processed_img)

        # Step 2: Extract text using EasyOCR reader
        reader = self._get_reader()
        raw_results = reader.readtext(processed_img)

        lines: List[OCRLineResult] = []
        full_text_pieces: List[str] = []

        for bbox_coords, text, conf in raw_results:
            clean_text = str(text).strip()
            if not clean_text:
                continue

            # bbox_coords is list of 4 points: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            pts = np.array(bbox_coords, dtype=int)
            x_min = int(np.min(pts[:, 0]))
            y_min = int(np.min(pts[:, 1]))
            x_max = int(np.max(pts[:, 0]))
            y_max = int(np.max(pts[:, 1]))

            line = OCRLineResult(
                text=clean_text,
                confidence=float(conf),
                bbox=OCRBoundingBox(
                    x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max
                ),
            )
            lines.append(line)
            full_text_pieces.append(clean_text)

        elapsed_ms = (time.time() - start_time) * 1000.0
        full_text = "\n".join(full_text_pieces)

        app_logger.info(
            f"EasyOCR extraction completed in {elapsed_ms:.1f}ms with {len(lines)} detected lines"
        )

        return OCRRawResult(
            engine_name=self.engine_name,
            lines=lines,
            full_text=full_text,
            processing_time_ms=elapsed_ms,
            metadata={"total_lines": len(lines)},
        )
