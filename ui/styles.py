"""
ui/styles.py
────────────
Injects the global CSS design system into the Streamlit app.
Call inject_styles() once at the top of main().
"""

import streamlit as st


def inject_styles() -> None:
    """Inject the full dark-mode CSS design system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400&display=swap');

        /* ── Base ── */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', sans-serif !important;
        }
        .stApp {
            background: linear-gradient(135deg, #0d0f1a 0%, #12152b 50%, #0d1520 100%) !important;
            color: #e8eaf0 !important;
            min-height: 100vh;
        }

        /* ── Streamlit text overrides ── */
        .stMarkdown p, .stMarkdown li, .stMarkdown span,
        .stText, p, li, span {
            color: #d1d5e8 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
        }
        label, .stSelectbox label, .stTextInput label,
        .stFileUploader label, .stToggle label {
            color: #a8b3d6 !important;
            font-weight: 600 !important;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #141728 0%, #0f1422 100%) !important;
            border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
        }
        [data-testid="stSidebar"] * {
            color: #c8cfe8 !important;
        }
        [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
            font-size: 0.85rem !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.8rem;
        }
        [data-testid="stSidebar"] .stSelectbox > div > div,
        [data-testid="stSidebar"] .stTextInput > div > div > input {
            background: rgba(255,255,255,0.06) !important;
            border: 1px solid rgba(99,102,241,0.2) !important;
            color: #e8eaf0 !important;
            border-radius: 12px !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(99,102,241,0.15) !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 0.7rem 0 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 28px rgba(99,102,241,0.5) !important;
        }

        /* ── st.metric ── */
        [data-testid="metric-container"] {
            background: transparent !important;
        }
        [data-testid="metric-container"] [data-testid="stMetricLabel"] {
            color: #a8b3d6 !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 2.4rem !important;
            font-weight: 800 !important;
        }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
            background: rgba(255,255,255,0.04) !important;
            border-radius: 16px;
            padding: 0.35rem;
            border: 1px solid rgba(99,102,241,0.12);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            border: none !important;
            border-radius: 12px !important;
            color: #8896bb !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            padding: 0.5rem 1.1rem !important;
            transition: all 0.2s ease !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(99,102,241,0.28), rgba(139,92,246,0.22)) !important;
            color: #c4b5fd !important;
            border: 1px solid rgba(99,102,241,0.25) !important;
        }
        .stTabs [data-baseweb="tab-panel"] {
            background: transparent !important;
            padding: 1rem 0 0 !important;
        }

        /* ── Alerts ── */
        .stAlert { border-radius: 14px !important; }
        [data-testid="stWarning"] {
            background: rgba(251,191,36,0.1) !important;
            border: 1px solid rgba(251,191,36,0.25) !important;
            color: #fef3c7 !important;
        }
        [data-testid="stSuccess"] {
            background: rgba(34,197,94,0.10) !important;
            border: 1px solid rgba(34,197,94,0.22) !important;
            color: #d1fae5 !important;
        }
        [data-testid="stInfo"] {
            background: rgba(99,102,241,0.10) !important;
            border: 1px solid rgba(99,102,241,0.20) !important;
            color: #e0e7ff !important;
        }
        [data-testid="stError"] {
            background: rgba(239,68,68,0.10) !important;
            border: 1px solid rgba(239,68,68,0.22) !important;
        }

        /* ── Dataframe ── */
        .stDataFrame {
            border-radius: 14px !important;
            overflow: hidden;
            border: 1px solid rgba(99,102,241,0.15) !important;
        }
        .stDataFrame thead tr th {
            background: rgba(99,102,241,0.15) !important;
            color: #c4b5fd !important;
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .stDataFrame tbody tr td {
            color: #d1d5e8 !important;
            background: rgba(255,255,255,0.02) !important;
            font-size: 0.85rem !important;
        }
        .stDataFrame tbody tr:hover td {
            background: rgba(99,102,241,0.08) !important;
        }

        /* ── File uploader ── */
        [data-testid="stFileUploader"] {
            background: rgba(255,255,255,0.03) !important;
            border: 1px dashed rgba(99,102,241,0.3) !important;
            border-radius: 16px !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: rgba(99,102,241,0.55) !important;
            background: rgba(99,102,241,0.05) !important;
        }

        /* ── Custom component styles ── */
        .hero-wrap {
            background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(139,92,246,0.08) 50%, rgba(56,189,248,0.06) 100%);
            border: 1px solid rgba(99,102,241,0.18);
            border-radius: 28px;
            padding: 2.5rem 3rem;
            margin-bottom: 2.5rem;
            position: relative;
            overflow: hidden;
        }
        .hero-wrap::before {
            content: '';
            position: absolute;
            top: -60px; right: -60px;
            width: 280px; height: 280px;
            background: radial-gradient(circle, rgba(139,92,246,0.18), transparent 70%);
            pointer-events: none;
        }
        .hero-wrap h1 {
            font-size: 2.6rem !important;
            font-weight: 900 !important;
            margin: 0 0 0.5rem !important;
            background: linear-gradient(135deg, #ffffff 0%, #c4b5fd 60%, #93c5fd 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.04em;
        }
        .hero-wrap p {
            margin: 0 !important;
            color: #8896bb !important;
            font-size: 1rem !important;
            max-width: 56rem;
            line-height: 1.6;
        }

        .section-heading {
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            letter-spacing: -0.01em;
            margin: 0 0 0.25rem !important;
        }
        .section-sub {
            font-size: 0.85rem !important;
            color: #6b7fa3 !important;
            margin: 0 0 1.2rem !important;
        }

        /* Stat cards */
        .metric-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.6rem;
        }
        .stat-card {
            flex: 1;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(99,102,241,0.14);
            border-radius: 20px;
            padding: 1.2rem 1.4rem;
            text-align: center;
        }
        .stat-card .stat-val {
            font-size: 2.6rem;
            font-weight: 900;
            color: #ffffff;
            line-height: 1;
            margin-bottom: 0.3rem;
        }
        .stat-card .stat-lbl {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #6b7fa3;
        }
        .stat-card.detections { border-color: rgba(99,102,241,0.3); }
        .stat-card.detections .stat-val { color: #a5b4fc; }
        .stat-card.passes { border-color: rgba(34,197,94,0.28); }
        .stat-card.passes .stat-val { color: #86efac; }
        .stat-card.severe { border-color: rgba(239,68,68,0.28); }
        .stat-card.severe .stat-val { color: #fca5a5; }

        /* Audit info strip */
        .audit-info-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 1.2rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(99,102,241,0.12);
            border-radius: 16px;
            padding: 1rem 1.3rem;
            margin-bottom: 1.2rem;
        }
        .audit-info-strip .info-item {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }
        .audit-info-strip .info-item .lbl {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #6b7fa3;
        }
        .audit-info-strip .info-item .val {
            font-size: 0.88rem;
            font-weight: 600;
            color: #d1d5e8;
        }

        /* Finding cards */
        .finding-card {
            border-radius: 16px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.75rem;
            border-left: 3px solid;
        }
        .finding-ok  { background: rgba(34,197,94,0.07);  border-color: #22c55e; }
        .finding-ok  .fc-title { color: #86efac; }
        .finding-warn { background: rgba(251,191,36,0.07); border-color: #fbbf24; }
        .finding-warn .fc-title { color: #fde68a; }
        .finding-bad  { background: rgba(239,68,68,0.08);  border-color: #ef4444; }
        .finding-bad  .fc-title { color: #fca5a5; }
        .fc-title  { font-size: 0.88rem; font-weight: 700; margin-bottom: 0.3rem; }
        .fc-meta   { font-size: 0.78rem; color: #8896bb; margin-bottom: 0.2rem; }
        .fc-result { font-size: 0.82rem; color: #c8cfe8; }

        /* Recommendation panel */
        .rec-header-card {
            background: linear-gradient(135deg, rgba(99,102,241,0.14), rgba(139,92,246,0.10));
            border: 1px solid rgba(99,102,241,0.22);
            border-radius: 20px;
            padding: 1.4rem 1.6rem;
            margin-bottom: 1.4rem;
        }
        .rec-header-card h2 {
            font-size: 1.5rem !important;
            font-weight: 800 !important;
            margin: 0 0 0.25rem !important;
            background: linear-gradient(135deg, #c4b5fd, #93c5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .rec-header-card p {
            margin: 0 !important;
            color: #6b7fa3 !important;
            font-size: 0.88rem !important;
        }
        .score-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 80px; height: 80px;
            border-radius: 50%;
            font-size: 1.8rem;
            font-weight: 900;
            box-shadow: 0 6px 24px rgba(0,0,0,0.3);
        }
        .score-good { background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; }
        .score-mid  { background: linear-gradient(135deg, #fbbf24, #d97706); color: #fff; }
        .score-bad  { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }
        .strength-item {
            background: rgba(34,197,94,0.08);
            border: 1px solid rgba(34,197,94,0.18);
            border-radius: 12px;
            padding: 0.6rem 0.9rem;
            margin-bottom: 0.5rem;
            font-size: 0.87rem;
            color: #bbf7d0;
        }
        .priority-item {
            background: rgba(99,102,241,0.08);
            border: 1px solid rgba(99,102,241,0.18);
            border-radius: 12px;
            padding: 0.65rem 0.9rem;
            margin-bottom: 0.5rem;
            font-size: 0.87rem;
            color: #e0e7ff;
        }
        .severity-badge {
            display: inline-block;
            padding: 0.1rem 0.5rem;
            border-radius: 8px;
            font-size: 0.68rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .sev-critical { background: rgba(239,68,68,0.2);   color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
        .sev-medium   { background: rgba(251,191,36,0.16);  color: #fde68a; border: 1px solid rgba(251,191,36,0.28); }
        .sev-low      { background: rgba(99,102,241,0.15);  color: #c4b5fd; border: 1px solid rgba(99,102,241,0.25); }
        .rec-issue-card {
            border-radius: 16px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.8rem;
            border-left: 3px solid;
        }
        .rec-critical { background: rgba(239,68,68,0.07);   border-color: #ef4444; }
        .rec-medium   { background: rgba(251,191,36,0.07);  border-color: #fbbf24; }
        .rec-low      { background: rgba(99,102,241,0.07);  border-color: #6366f1; }
        .rec-issue-card strong { color: #e8eaf0; }
        .rec-issue-card em { color: #6b7fa3; font-size: 0.8rem; }
        .rec-issue-card .issue-text { color: #c8cfe8; font-size: 0.87rem; margin-top: 0.3rem; }
        .rec-divider {
            height: 1px;
            background: linear-gradient(to right, transparent, rgba(99,102,241,0.25), transparent);
            margin: 1.4rem 0;
        }
        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: #6b7fa3;
            font-size: 0.95rem;
        }
        .empty-state .icon { font-size: 3rem; margin-bottom: 0.75rem; display: block; }
        </style>
        """,
        unsafe_allow_html=True,
    )
