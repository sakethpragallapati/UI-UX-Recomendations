"""
core/detector.py
────────────────
Detection pipeline: runs YOLO + EasyOCR + UIAuditor on an image
and returns structured detection results with an annotated frame.
"""

import os
from typing import Dict, List

import cv2

from core.resources import load_auditor, load_detector, load_reader


# BGR colours used when drawing bounding boxes on the annotated image
DETECTION_COLORS: Dict[str, tuple] = {
    "general_button": (99, 102, 241),
    "general_link":   (34, 197, 94),
    "general_input":  (251, 146, 60),
    "general_image":  (168, 85, 247),
    "icon_search":    (251, 191, 36),
    "icon_menu":      (56, 189, 248),
}

_DEFAULT_COLOR = (99, 102, 241)


def draw_detections(image_bgr, detections: List[Dict]):
    """
    Draw labelled bounding boxes on a copy of *image_bgr* and return
    an RGB numpy array suitable for ``st.image``.
    """
    canvas = image_bgr.copy()
    for item in detections:
        x1, y1, x2, y2 = item["xyxy"]
        label = item["yolo_class"]
        color = DETECTION_COLORS.get(label, _DEFAULT_COLOR)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        cv2.rectangle(
            canvas,
            (x1, max(0, y1 - 26)),
            (min(canvas.shape[1] - 1, x1 + 220), y1),
            color, -1,
        )
        cv2.putText(
            canvas, label, (x1 + 6, max(16, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.52,
            (255, 255, 255), 1, cv2.LINE_AA,
        )
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)


def run_ui_audit(
    image_path: str,
    selected_category: str,
    det_weights_path: str,
) -> Dict:
    """
    Run the full detection + audit pipeline on *image_path*.

    Returns a dict with keys:
        annotated_image, detections, total_detections,
        pass_count, severe_count, image_width, image_height
    """
    if not os.path.exists(det_weights_path):
        raise FileNotFoundError(
            f"Detector weights not found at '{det_weights_path}'."
        )

    detector = load_detector(det_weights_path)
    reader   = load_reader()
    auditor  = load_auditor()

    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError(f"Could not read image at '{image_path}'.")

    img_h, img_w = image_bgr.shape[:2]
    results = detector(image_path, verbose=False)

    detections: List[Dict] = []
    severe_count = 0
    pass_count   = 0

    for box in results[0].boxes:
        class_id   = int(box.cls[0])
        yolo_class = detector.names[class_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x_center = float(box.xywhn[0][0])
        ocr_text = ""

        if "general_" in yolo_class:
            cropped = image_bgr[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
            if cropped.size != 0:
                ocr_results = reader.readtext(cropped, detail=0)
                ocr_text = " ".join(ocr_results).strip().lower()

        audit_result = auditor.audit_element(
            predicted_categories=[selected_category],
            yolo_class=yolo_class,
            x_center=x_center,
            ocr_text=ocr_text,
            confidence=100.0,
        )

        if "SEVERE ANOMALY" in audit_result or "ARCHITECTURAL ANOMALY" in audit_result:
            severe_count += 1
        else:
            pass_count += 1

        detections.append({
            "yolo_class":   yolo_class,
            "confidence":   confidence,
            "ocr_text":     ocr_text,
            "audit_result": audit_result,
            "xyxy":         (x1, y1, x2, y2),
        })

    annotated = draw_detections(image_bgr, detections)
    return {
        "annotated_image":  annotated,
        "detections":       detections,
        "total_detections": len(detections),
        "pass_count":       pass_count,
        "severe_count":     severe_count,
        "image_width":      img_w,
        "image_height":     img_h,
    }
