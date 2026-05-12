import os
import tempfile
from pathlib import Path

import cv2
import easyocr
import numpy as np
import streamlit as st
from PIL import Image
from ultralytics import YOLO

from auditor import UIAuditor


st.set_page_config(
    page_title="UI Audit Studio",
    page_icon="UI",
    layout="wide",
    initial_sidebar_state="expanded",
)


DETECTION_COLORS = {
    "general_button": (18, 107, 240),
    "general_link": (51, 153, 102),
    "general_input": (255, 140, 66),
    "general_image": (156, 39, 176),
    "icon_search": (225, 112, 85),
    "icon_menu": (0, 121, 140),
}


def inject_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 217, 179, 0.55), transparent 30%),
                radial-gradient(circle at top right, rgba(171, 214, 255, 0.5), transparent 28%),
                linear-gradient(180deg, #f7f2ea 0%, #f4f6fb 45%, #eef4f1 100%);
            color: #1f2933;
        }
        .hero {
            padding: 1.6rem 1.8rem;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(31, 41, 51, 0.08);
            box-shadow: 0 20px 45px rgba(57, 72, 89, 0.10);
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
        }
        .hero h1 {
            font-size: 2.3rem;
            margin: 0;
            letter-spacing: -0.03em;
        }
        .hero p {
            margin: 0.55rem 0 0;
            max-width: 52rem;
            color: #52606d;
            font-size: 1rem;
        }
        .metric-card {
            padding: 1rem 1.1rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(31, 41, 51, 0.08);
            box-shadow: 0 14px 34px rgba(57, 72, 89, 0.08);
        }
        .panel-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.6rem;
        }
        .audit-ok {
            padding: 0.8rem 0.9rem;
            border-radius: 16px;
            background: rgba(221, 245, 228, 0.9);
            border: 1px solid rgba(67, 160, 71, 0.2);
            margin-bottom: 0.6rem;
        }
        .audit-warn {
            padding: 0.8rem 0.9rem;
            border-radius: 16px;
            background: rgba(255, 239, 213, 0.92);
            border: 1px solid rgba(255, 167, 38, 0.24);
            margin-bottom: 0.6rem;
        }
        .audit-bad {
            padding: 0.8rem 0.9rem;
            border-radius: 16px;
            background: rgba(255, 228, 225, 0.94);
            border: 1px solid rgba(229, 57, 53, 0.18);
            margin-bottom: 0.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def load_detector(weights_path):
    return YOLO(weights_path)


@st.cache_resource
def load_reader():
    return easyocr.Reader(["en"], gpu=False)


@st.cache_resource
def load_auditor():
    return UIAuditor()


def get_available_categories(baseline_file="ui_baseline_rules.json"):
    auditor = load_auditor()
    return sorted(auditor.baselines.keys())


def normalize_result_text(result):
    if "SEVERE ANOMALY" in result or "ARCHITECTURAL ANOMALY" in result:
        return "audit-bad"
    if "ERROR" in result:
        return "audit-warn"
    return "audit-ok"


def draw_detections(image_bgr, detections):
    canvas = image_bgr.copy()
    for item in detections:
        x1, y1, x2, y2 = item["xyxy"]
        label = item["yolo_class"]
        color = DETECTION_COLORS.get(label, (47, 84, 235))
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        cv2.rectangle(canvas, (x1, max(0, y1 - 26)), (min(canvas.shape[1] - 1, x1 + 220), y1), color, -1)
        cv2.putText(
            canvas,
            label,
            (x1 + 6, max(16, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)


def run_ui_audit(image_path, selected_category, det_weights_path="runs/detect/ui_detector2/weights/best.pt"):
    if not os.path.exists(det_weights_path):
        raise FileNotFoundError(f"Detector weights not found at '{det_weights_path}'.")

    detector = load_detector(det_weights_path)
    reader = load_reader()
    auditor = load_auditor()

    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError(f"Could not read image at '{image_path}'.")

    results = detector(image_path, verbose=False)

    detections = []
    severe_count = 0
    pass_count = 0

    for box in results[0].boxes:
        class_id = int(box.cls[0])
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

        detections.append(
            {
                "yolo_class": yolo_class,
                "confidence": confidence,
                "ocr_text": ocr_text,
                "audit_result": audit_result,
                "xyxy": (x1, y1, x2, y2),
            }
        )

    annotated = draw_detections(image_bgr, detections)
    return {
        "annotated_image": annotated,
        "detections": detections,
        "total_detections": len(detections),
        "pass_count": pass_count,
        "severe_count": severe_count,
    }


def render_header():
    st.markdown(
        """
        <div class="hero">
            <h1>UI Audit Studio</h1>
            <p>Upload a Figma frame or website screenshot, choose the website type, and inspect how the detector reads the interface against your baseline UX rules.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_detection_cards(result):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Detections", result["total_detections"])
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Pass / Safe", result["pass_count"])
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Severe Findings", result["severe_count"])
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    inject_styles()
    render_header()

    categories = get_available_categories()
    if not categories:
        st.error("No categories found in 'ui_baseline_rules.json'. Run analyzer.py first.")
        return

    with st.sidebar:
        st.markdown("### Session Setup")
        selected_category = st.selectbox(
            "Website type",
            options=categories,
            help="These options come directly from ui_baseline_rules.json.",
        )
        det_weights_path = st.text_input(
            "Detector weights path",
            value="runs/detect/ui_detector2/weights/best.pt",
        )
        uploaded_file = st.file_uploader(
            "Upload a Figma or website image",
            type=["png", "jpg", "jpeg", "webp"],
        )
        run_button = st.button("Run Audit", use_container_width=True, type="primary")

    preview_col, results_col = st.columns([1.1, 1.2], gap="large")

    image_bytes = uploaded_file.read() if uploaded_file else None
    if uploaded_file is not None:
        uploaded_file.seek(0)

    with preview_col:
        st.markdown('<div class="panel-title">Source Preview</div>', unsafe_allow_html=True)
        if image_bytes:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, use_container_width=True, caption=f"Selected type: {selected_category}")
        else:
            st.info("Upload a Figma export or website screenshot to start.")

    with results_col:
        st.markdown('<div class="panel-title">Audit Results</div>', unsafe_allow_html=True)
        if run_button:
            if not image_bytes:
                st.warning("Upload an image first.")
                return

            suffix = Path(uploaded_file.name).suffix or ".png"
            temp_dir = os.path.join(os.getcwd(), "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir) as tmp_file:
                tmp_file.write(image_bytes)
                temp_path = tmp_file.name

            try:
                with st.spinner("Running detector, OCR, and baseline audit..."):
                    result = run_ui_audit(
                        image_path=temp_path,
                        selected_category=selected_category,
                        det_weights_path=det_weights_path,
                    )

                render_detection_cards(result)
                st.image(
                    result["annotated_image"],
                    use_container_width=True,
                    caption="Detected UI elements with bounding boxes",
                )

                st.markdown('<div class="panel-title">Element Review</div>', unsafe_allow_html=True)
                if not result["detections"]:
                    st.info("No UI elements were detected in this image.")
                else:
                    for item in result["detections"]:
                        ocr_display = item["ocr_text"] if item["ocr_text"] else "Visual icon / no OCR text"
                        css_class = normalize_result_text(item["audit_result"])
                        st.markdown(
                            f"""
                            <div class="{css_class}">
                                <strong>{item['yolo_class']}</strong> · confidence {item['confidence']:.2f}<br/>
                                OCR: {ocr_display}<br/>
                                {item['audit_result']}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            except Exception as exc:
                st.error(str(exc))
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        else:
            st.info("Choose a website type, upload an image, and press 'Run Audit'.")


if __name__ == "__main__":
    main()
