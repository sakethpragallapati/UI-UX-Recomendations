"""
core/resources.py
─────────────────
Streamlit-cached singleton loaders for heavy ML resources.
Import these functions instead of instantiating models directly
so that Streamlit only loads each resource once per server process.
"""

import streamlit as st
from ultralytics import YOLO
import easyocr

from auditor import UIAuditor
from recommender import RecommendationEngine


@st.cache_resource
def load_detector(weights_path: str) -> YOLO:
    """Load (and cache) the YOLO detector from a weights file."""
    return YOLO(weights_path)


@st.cache_resource
def load_reader() -> easyocr.Reader:
    """Load (and cache) the EasyOCR reader (CPU mode)."""
    return easyocr.Reader(["en"], gpu=False)


@st.cache_resource
def load_auditor() -> UIAuditor:
    """Load (and cache) the UIAuditor with baseline rules."""
    return UIAuditor()


@st.cache_resource
def load_recommender() -> RecommendationEngine:
    """Load (and cache) the LLM recommendation engine."""
    return RecommendationEngine()


def get_available_categories() -> list[str]:
    """Return sorted list of website categories from the baseline rules."""
    return sorted(load_auditor().baselines.keys())
