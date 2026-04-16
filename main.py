"""
main.py
───────
Entry point for UI Audit Studio.

Run with:
    streamlit run main.py

Responsibilities of this file:
  - Page configuration (must be the very first Streamlit call)
  - Session-state initialisation
  - Sidebar widgets
  - Orchestrating the audit pipeline
  - Rendering results by delegating to ui.components
"""

import io
import os
import tempfile
from pathlib import Path

import streamlit as st

# ── Page config must come before any other st.* call ──────────────────────────
st.set_page_config(
    page_title="UI Audit Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local modules ──────────────────────────────────────────────────────────────
from core.detector import run_ui_audit
from core.resources import (
    get_available_categories,
    load_auditor,
    load_recommender,
)
from ui.components import (
    finding_css_class,
    render_annotated_image,
    render_audit_info_strip,
    render_detection_table,
    render_empty_state,
    render_findings,
    render_header,
    render_recommendations,
    render_source_preview,
    render_stat_cards,
)
from ui.styles import inject_styles

_DIVIDER = '<hr style="border-color:rgba(99,102,241,0.12);margin:2rem 0;">'


def main() -> None:
    inject_styles()
    render_header()

    # ── Session state ──────────────────────────────────────────────────────────
    for key in ("audit_result", "audit_image_name", "audit_category", "audit_recommendations"):
        if key not in st.session_state:
            st.session_state[key] = None

    # ── Category check ─────────────────────────────────────────────────────────
    categories = get_available_categories()
    if not categories:
        st.error("No categories found in 'ui_baseline_rules.json'. Run analyzer.py first.")
        return

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Session Setup")
        selected_category = st.selectbox(
            "Website type",
            options=categories,
            help="Pulled directly from ui_baseline_rules.json.",
        )
        det_weights_path = st.text_input(
            "Detector weights path",
            value="runs/detect/ui_detector/weights/best.pt",
        )
        uploaded_file = st.file_uploader(
            "Upload a Figma or website image",
            type=["png", "jpg", "jpeg", "webp"],
        )

        st.markdown("---")
        st.markdown("### 🤖 AI Recommendations")
        enable_recommendations = st.toggle(
            "Enable LLM Recommendations",
            value=True,
            help="Generate AI-powered UX suggestions after audit.",
        )

        recommender = load_recommender()
        if enable_recommendations and not recommender.is_available:
            st.warning(
                "⚠️ No HUGGINGFACEHUB_ACCESS_TOKEN found in `.env`. "
                "Rule-based fallback will be used."
            )

        run_button = st.button("▶ Run Audit", use_container_width=True, type="primary")

    # ── Read uploaded bytes safely (avoids exhausted file-pointer on re-render) ─
    image_bytes = uploaded_file.read() if uploaded_file else None
    if uploaded_file is not None:
        uploaded_file.seek(0)

    # ── Run audit pipeline on button press ────────────────────────────────────
    if run_button:
        if not image_bytes:
            st.warning("Upload an image first.")
            return

        suffix = Path(uploaded_file.name).suffix or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(image_bytes)
            temp_path = tmp.name

        try:
            with st.spinner("Running detector, OCR, and baseline audit…"):
                result = run_ui_audit(
                    image_path=temp_path,
                    selected_category=selected_category,
                    det_weights_path=det_weights_path,
                )

            st.session_state.audit_result = result
            st.session_state.audit_image_name = uploaded_file.name
            st.session_state.audit_category = selected_category
            st.session_state.audit_recommendations = None

            if enable_recommendations and result["detections"]:
                with st.spinner("Generating AI recommendations…"):
                    auditor = load_auditor()
                    rec = recommender.generate_recommendations(
                        detections=result["detections"],
                        category=selected_category,
                        baselines=auditor.baselines,
                        image_path=temp_path,
                        image_width=result["image_width"],
                        image_height=result["image_height"],
                    )
                st.session_state.audit_recommendations = rec

        except Exception as exc:
            st.error(str(exc))
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    # ── Pull results from session state ───────────────────────────────────────
    result    = st.session_state.audit_result
    saved_rec = st.session_state.audit_recommendations

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE LAYOUT  (single-column flow)
    #   1. Source preview
    #   2. Audit summary (metrics)
    #   3. Annotated image
    #   4. Info strip + tabbed detail panel
    # ══════════════════════════════════════════════════════════════════════════

    # 1. Source preview
    if image_bytes:
        render_source_preview(image_bytes, selected_category)
    elif result:
        st.info(f"Last analysed file: **{st.session_state.audit_image_name}**")
    else:
        render_empty_state()

    # 2 – 4. Results section
    if result:
        st.markdown(_DIVIDER, unsafe_allow_html=True)

        # 2. Summary metrics + status
        st.markdown(
            '<div class="section-heading">📊 Audit Summary</div>'
            '<div class="section-sub">High-level snapshot of the detection run.</div>',
            unsafe_allow_html=True,
        )
        render_stat_cards(result)
        if result["severe_count"]:
            st.warning(f"⚠️  **{result['severe_count']} severe issues** detected — review the Findings tab below.")
        else:
            st.success("✅  No severe anomalies detected — layout is looking good!")

        st.markdown(_DIVIDER, unsafe_allow_html=True)

        # 3. Annotated image
        render_annotated_image(result["annotated_image"])

        st.markdown(_DIVIDER, unsafe_allow_html=True)

        # 4a. Metadata strip
        render_audit_info_strip(
            category=st.session_state.audit_category,
            image_name=st.session_state.audit_image_name,
            image_width=result["image_width"],
            image_height=result["image_height"],
            ai_enabled=enable_recommendations,
        )

        # 4b. Tabbed detail panel
        table_tab, findings_tab, rec_tab = st.tabs(
            ["📋 Element Table", "🚨 Findings", "✨ Recommendations"]
        )

        with table_tab:
            st.markdown(
                '<div class="section-sub" style="margin-bottom:0.8rem;">'
                'All detected elements with confidence scores and audit verdicts.</div>',
                unsafe_allow_html=True,
            )
            if result["detections"]:
                render_detection_table(result["detections"])
            else:
                st.info("No UI elements were detected in this image.")

        with findings_tab:
            render_findings(result["detections"])

        with rec_tab:
            if enable_recommendations and result["detections"]:
                if saved_rec:
                    render_recommendations(saved_rec)
                else:
                    st.warning("Could not generate recommendations. Check your API key in `.env`.")
            else:
                st.info("Enable recommendations in the sidebar and run an audit to see UX suggestions.")


if __name__ == "__main__":
    main()
