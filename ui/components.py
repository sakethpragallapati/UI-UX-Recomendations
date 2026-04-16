"""
ui/components.py
────────────────
All Streamlit render helpers for UI Audit Studio.
Each function is self-contained and side-effect-free except for
calling st.* to emit HTML/widgets.
"""

from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from recommender import AuditRecommendation


# ─── Utility ───────────────────────────────────────────────────────────────────

_DIVIDER = '<hr style="border-color:rgba(99,102,241,0.12);margin:2rem 0;">'
_REC_DIVIDER = '<div class="rec-divider"></div>'


def _hr() -> None:
    st.markdown(_DIVIDER, unsafe_allow_html=True)


def finding_css_class(result_text: str) -> str:
    """Map an audit verdict string to the correct CSS card class."""
    if "SEVERE ANOMALY" in result_text or "ARCHITECTURAL ANOMALY" in result_text:
        return "finding-bad"
    if "ERROR" in result_text or "ANOMALY" in result_text:
        return "finding-warn"
    return "finding-ok"


# ─── Header ────────────────────────────────────────────────────────────────────

def render_header() -> None:
    """Render the hero banner at the top of the page."""
    st.markdown(
        """
        <div class="hero-wrap">
            <h1>🎨 UI Audit Studio</h1>
            <p>
                Upload a Figma frame or website screenshot, select the site type, and instantly
                detect UI element placements against your baseline UX rules.
                Get AI-powered recommendations to elevate your design.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Source preview ─────────────────────────────────────────────────────────────

def render_source_preview(image_bytes: bytes, selected_category: str) -> None:
    """Display the original uploaded image centred on the page."""
    from PIL import Image
    import io

    st.markdown(
        '<div class="section-heading">🖼️ Source Preview</div>'
        '<div class="section-sub">Your uploaded design — results are anchored to this frame.</div>',
        unsafe_allow_html=True,
    )
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    _, mid, _ = st.columns([1, 6, 1])
    with mid:
        st.image(pil_img, use_container_width=True, caption=f"Type: {selected_category}")


def render_empty_state() -> None:
    """Show a call-to-action when no image has been uploaded yet."""
    st.markdown(
        '<div class="empty-state">'
        '<span class="icon">📤</span>'
        'Upload a Figma export or website screenshot and press '
        '<strong>▶ Run Audit</strong>&nbsp;in the sidebar.'
        '</div>',
        unsafe_allow_html=True,
    )


# ─── Stat cards ─────────────────────────────────────────────────────────────────

def render_stat_cards(result: Dict) -> None:
    """Render the three colour-coded metric cards (detections / passes / severe)."""
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="stat-card detections">
                <div class="stat-val">{result['total_detections']}</div>
                <div class="stat-lbl">Detections</div>
            </div>
            <div class="stat-card passes">
                <div class="stat-val">{result['pass_count']}</div>
                <div class="stat-lbl">Pass / Safe</div>
            </div>
            <div class="stat-card severe">
                <div class="stat-val">{result['severe_count']}</div>
                <div class="stat-lbl">Severe Issues</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Annotated image ────────────────────────────────────────────────────────────

def render_annotated_image(annotated_image) -> None:
    """Render the YOLO-annotated image centred on the page."""
    st.markdown(
        '<div class="section-heading">🔎 Detected Elements</div>'
        '<div class="section-sub">Bounding boxes drawn over each identified UI element.</div>',
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 6, 1])
    with mid:
        st.image(
            annotated_image,
            use_container_width=True,
            caption="Annotated detections",
        )


# ─── Info strip ─────────────────────────────────────────────────────────────────

def render_audit_info_strip(
    category: str,
    image_name: str,
    image_width: int,
    image_height: int,
    ai_enabled: bool,
) -> None:
    """Render the horizontal metadata strip above the tabs."""
    ai_val  = "Enabled" if ai_enabled else "Disabled"
    size_val = f"{image_width} × {image_height} px"
    st.markdown(
        f"""
        <div class="audit-info-strip">
            <div class="info-item">
                <span class="lbl">Website Type</span>
                <span class="val">{category or "—"}</span>
            </div>
            <div class="info-item">
                <span class="lbl">Image</span>
                <span class="val">{image_name or "Uploaded frame"}</span>
            </div>
            <div class="info-item">
                <span class="lbl">Dimensions</span>
                <span class="val">{size_val}</span>
            </div>
            <div class="info-item">
                <span class="lbl">AI Mode</span>
                <span class="val">{ai_val}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Detection table ────────────────────────────────────────────────────────────

def render_detection_table(detections: List[Dict]) -> None:
    """Render a styled dataframe of all detected elements."""
    rows = [
        {
            "Element":      d["yolo_class"],
            "Conf":         f"{d['confidence']:.2f}",
            "OCR Text":     d["ocr_text"] or "—",
            "Audit Result": d["audit_result"],
        }
        for d in detections
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─── Findings tab ───────────────────────────────────────────────────────────────

def render_findings(detections: List[Dict]) -> None:
    """Render per-element finding cards with colour-coded severity."""
    if not detections:
        st.info("No UI elements were detected in this image.")
        return

    for item in detections:
        ocr_display = item["ocr_text"] if item["ocr_text"] else "Visual icon / no text"
        css = finding_css_class(item["audit_result"])
        st.markdown(
            f"""
            <div class="finding-card {css}">
                <div class="fc-title">{item['yolo_class']}</div>
                <div class="fc-meta">Confidence: {item['confidence']:.2f} &nbsp;|&nbsp; OCR: {ocr_display}</div>
                <div class="fc-result">{item['audit_result']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─── Recommendations tab ─────────────────────────────────────────────────────────

def render_recommendations(rec: AuditRecommendation) -> None:
    """Render the full AI recommendation panel."""
    score     = rec.overall_score
    score_cls = "score-good" if score >= 75 else "score-mid" if score >= 45 else "score-bad"

    # Header
    st.markdown(
        """
        <div class="rec-header-card">
            <h2>✨ AI Recommendations</h2>
            <p>LLM-powered UX analysis of your detected elements and layout patterns.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Score + summary
    score_col, summary_col = st.columns([1, 3], gap="large")
    with score_col:
        st.markdown(
            f'<div style="display:flex;flex-direction:column;align-items:center;padding-top:0.3rem;">'
            f'<div class="score-badge {score_cls}">{score}</div>'
            f'<div style="margin-top:0.6rem;font-size:0.75rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.06em;color:#6b7fa3;">UX Score</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with summary_col:
        st.markdown(
            f'<p style="color:#c8cfe8;line-height:1.65;margin:0;">'
            f'<strong style="color:#ffffff;">Summary:</strong> {rec.summary}</p>',
            unsafe_allow_html=True,
        )

    st.markdown(_REC_DIVIDER, unsafe_allow_html=True)

    # Priority actions
    if rec.priority_actions:
        st.markdown('<div class="section-heading">🎯 Priority Actions</div>', unsafe_allow_html=True)
        for i, action in enumerate(rec.priority_actions, 1):
            st.markdown(
                f'<div class="priority-item"><strong style="color:#a5b4fc;">{i}.</strong> {action}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(_REC_DIVIDER, unsafe_allow_html=True)

    # Strengths
    if rec.strengths:
        st.markdown('<div class="section-heading">💪 Strengths</div>', unsafe_allow_html=True)
        for s in rec.strengths:
            st.markdown(f'<div class="strength-item">✅ {s}</div>', unsafe_allow_html=True)
        st.markdown(_REC_DIVIDER, unsafe_allow_html=True)

    # Per-element issues
    if rec.recommendations:
        st.markdown('<div class="section-heading">🔍 Detailed Findings</div>', unsafe_allow_html=True)
        for item in rec.recommendations:
            sev       = item.severity.lower()
            card_cls  = f"rec-{sev}"  if sev in ("critical", "medium", "low") else "rec-low"
            badge_cls = f"sev-{sev}"  if sev in ("critical", "medium", "low") else "sev-low"
            st.markdown(
                f"""
                <div class="rec-issue-card {card_cls}">
                    <span class="severity-badge {badge_cls}">{item.severity}</span>
                    <strong style="margin-left:0.5rem;">{item.element_class}</strong>
                    <div class="issue-text">
                        <strong style="color:#a5b4fc;">Issue:</strong> {item.issue}<br/>
                        <strong style="color:#86efac;">Fix:</strong> {item.recommendation}<br/>
                        <em>Principle: {item.ux_principle}</em>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.success("No specific issues found — your UI matches expected conventions! 🎉")
