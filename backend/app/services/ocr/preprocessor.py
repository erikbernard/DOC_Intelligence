"""Image Preprocessing and Perspective Correction using OpenCV."""

import io
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from app.core.logging import app_logger


def bytes_to_numpy(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes to an OpenCV BGR numpy array."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image bytes with OpenCV.")
    return img


def numpy_to_bytes(image_np: np.ndarray, extension: str = ".jpg") -> bytes:
    """Encode OpenCV numpy array into bytes."""
    success, buffer = cv2.imencode(extension, image_np)
    if not success:
        raise ValueError("Failed to encode image array to bytes.")
    return buffer.tobytes()


def order_points(pts: np.ndarray) -> np.ndarray:
    """Order coordinates in clockwise order: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Apply perspective transform to crop and align document bounding polygon."""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute width of new image
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))

    # Compute height of new image
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))

    if max_width < 100 or max_height < 100:
        return image

    dst = np.array(
        [
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1],
        ],
        dtype="float32",
    )

    m = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, m, (max_width, max_height))
    return warped


def auto_deskew_and_crop(image: np.ndarray) -> np.ndarray:
    """Detect dominant quadrilateral in image and rectify perspective."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)

        contours, _ = cv2.findContours(
            edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            # If quadrilateral found and represents at least 20% of image area
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                img_area = image.shape[0] * image.shape[1]
                if area > 0.20 * img_area:
                    app_logger.info("Quadrilateral document contour detected. Applying deskew transform.")
                    return four_point_transform(image, approx.reshape(4, 2))
        return image
    except Exception as exc:
        app_logger.warning(f"Deskew preprocessing warning: {str(exc)}")
        return image


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Apply adaptive histogram equalization (CLAHE) for clean contrast."""
    try:
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l_channel)
            limg = cv2.merge((cl, a, b))
            return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)
    except Exception:
        return image
