import json
import html
import os
import time

import pandas as pd
import streamlit as st

from etl import ETLPipeline
from logger import setup_logger
from s3_handler import S3Handler
from utils import load_config, log_pipeline_run


logger = setup_logger()
config = load_config()
pipeline = ETLPipeline(config=config, logger=logger)
s3 = S3Handler(config=config, logger=logger)

st.set_page_config(
    page_title="CloudForge",
    page_icon="CF",
    layout="wide"
)

st.markdown(
    """
    <style>
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes fadeSlideUp {
            from {
                opacity: 0;
                transform: translateY(14px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes pulseGlow {
            0%, 100% {
                box-shadow: 0 0 18px rgba(0, 255, 255, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.14);
            }
            50% {
                box-shadow: 0 0 32px rgba(0, 114, 255, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.2);
            }
        }
        @keyframes textFlow {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }
        @keyframes shimmerSweep {
            0% { transform: translateX(-140%) skewX(-18deg); }
            100% { transform: translateX(180%) skewX(-18deg); }
        }
        :root {
            --cf-bg-1: #050816;
            --cf-bg-2: #07111f;
            --cf-bg-3: #11103a;
            --cf-cyan: #00ffff;
            --cf-blue: #0072ff;
            --cf-green: #00ff99;
            --cf-pink: #ff3d81;
            --cf-purple: #8b5cf6;
            --cf-text: #f8fbff;
            --cf-muted: #a7b4c8;
            --cf-border: rgba(255, 255, 255, 0.16);
            --cf-glass: rgba(8, 16, 34, 0.68);
            --cf-glass-strong: rgba(12, 22, 45, 0.82);
        }
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(0, 255, 255, 0.16), transparent 32%),
                radial-gradient(circle at top right, rgba(255, 61, 129, 0.12), transparent 30%),
                linear-gradient(125deg, var(--cf-bg-1), var(--cf-bg-2), var(--cf-bg-3), #04121f);
            background-size: 220% 220%;
            animation: gradientShift 24s ease infinite;
            color: var(--cf-text);
        }
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
            background-size: 34px 34px;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,0.9), rgba(0,0,0,0.25));
        }
        [data-testid="stHeader"] {
            background: linear-gradient(90deg, rgba(5, 8, 22, 0.94), rgba(17, 16, 58, 0.88)) !important;
            border-bottom: 1px solid rgba(0, 255, 255, 0.12);
            backdrop-filter: blur(18px);
        }
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {
            background: transparent !important;
        }
        [data-testid="stToolbar"] * {
            color: var(--cf-muted) !important;
        }
        [data-testid="stSidebar"] {
            background: rgba(4, 10, 24, 0.82);
            border-right: 1px solid rgba(0, 255, 255, 0.12);
            backdrop-filter: blur(20px);
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: var(--cf-text) !important;
        }
        h1, h2, h3 {
            color: var(--cf-text);
            letter-spacing: 0;
        }
        .cf-header {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(0, 255, 255, 0.18);
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(8, 18, 38, 0.82), rgba(22, 18, 58, 0.58));
            backdrop-filter: blur(20px);
            padding: 1.25rem 1.45rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.14);
            animation: fadeSlideUp 0.55s ease both;
        }
        .cf-header::after,
        .cf-card::after,
        .cf-panel::after,
        .cf-log-card::after {
            content: "";
            position: absolute;
            top: 0;
            left: -120%;
            width: 48%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.14), transparent);
            transform: skewX(-18deg);
            transition: transform 0.5s ease;
        }
        .cf-header:hover::after,
        .cf-card:hover::after,
        .cf-panel:hover::after,
        .cf-log-card:hover::after {
            animation: shimmerSweep 0.9s ease;
        }
        .cf-title {
            font-size: 2.05rem;
            font-weight: 800;
            color: var(--cf-text);
            margin-bottom: 0.15rem;
            background: linear-gradient(90deg, #ffffff, var(--cf-cyan), var(--cf-green), #ffffff);
            background-size: 220% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: textFlow 6s linear infinite;
        }
        .cf-subtitle {
            font-size: 0.95rem;
            color: var(--cf-muted);
            margin-bottom: 1.25rem;
        }
        .cf-section {
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            padding-top: 1.15rem;
            margin-top: 1.4rem;
            margin-bottom: 0.75rem;
            animation: fadeSlideUp 0.45s ease both;
        }
        .cf-section-title {
            font-size: 1.08rem;
            font-weight: 800;
            color: var(--cf-text);
            margin-bottom: 0.2rem;
        }
        .cf-section-caption {
            font-size: 0.86rem;
            color: var(--cf-muted);
            margin-bottom: 0.85rem;
        }
        .cf-card {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(0, 255, 255, 0.16);
            border-radius: 18px;
            padding: 1rem;
            background: linear-gradient(145deg, rgba(10, 22, 46, 0.74), rgba(15, 23, 42, 0.42));
            backdrop-filter: blur(18px);
            min-height: 112px;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.13);
            transition: transform 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
            animation: fadeSlideUp 0.5s ease both, pulseGlow 4.5s ease-in-out infinite;
        }
        .cf-card:hover {
            transform: translateY(-6px) scale(1.015);
            border-color: rgba(0, 255, 255, 0.5);
            box-shadow: 0 24px 70px rgba(0, 114, 255, 0.22), 0 0 26px rgba(0, 255, 255, 0.18);
        }
        .cf-card-label {
            font-size: 0.75rem;
            color: var(--cf-muted);
            font-weight: 750;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }
        .cf-card-value {
            font-size: 1.65rem;
            line-height: 1.2;
            font-weight: 820;
            color: var(--cf-text);
            word-break: break-word;
            background: linear-gradient(90deg, var(--cf-cyan), var(--cf-blue), var(--cf-green), var(--cf-cyan));
            background-size: 240% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: textFlow 5s linear infinite;
        }
        .cf-card-note {
            font-size: 0.78rem;
            color: var(--cf-muted);
            margin-top: 0.45rem;
        }
        .cf-panel {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(10, 22, 46, 0.78), rgba(9, 14, 30, 0.56));
            backdrop-filter: blur(18px);
            padding: 1rem;
            min-height: 220px;
            box-shadow: 0 18px 60px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.12);
            transition: transform 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease;
        }
        .cf-panel:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 255, 255, 0.34);
            box-shadow: 0 26px 80px rgba(0, 114, 255, 0.18), 0 0 24px rgba(139, 92, 246, 0.18);
        }
        .cf-panel-title {
            font-size: 0.92rem;
            font-weight: 800;
            color: var(--cf-text);
            margin-bottom: 0.25rem;
        }
        .cf-panel-caption {
            font-size: 0.78rem;
            color: var(--cf-muted);
            margin-bottom: 0.85rem;
        }
        .cf-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 0.18rem 0.55rem;
            font-size: 0.72rem;
            font-weight: 700;
            margin-right: 0.35rem;
        }
        .cf-pill-success {
            background: rgba(0, 255, 153, 0.14);
            color: var(--cf-green);
            border: 1px solid rgba(0, 255, 153, 0.24);
        }
        .cf-pill-failed {
            background: rgba(255, 61, 129, 0.13);
            color: #ff8ab2;
            border: 1px solid rgba(255, 61, 129, 0.24);
        }
        .cf-bar-track {
            width: 100%;
            height: 14px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(255, 61, 129, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.14);
            margin-top: 0.9rem;
        }
        .cf-bar-success {
            height: 14px;
            background: linear-gradient(90deg, var(--cf-green), var(--cf-cyan));
            box-shadow: 0 0 18px rgba(0, 255, 153, 0.35);
        }
        .cf-runtime-row {
            display: grid;
            grid-template-columns: 72px 1fr 64px;
            gap: 0.6rem;
            align-items: center;
            margin: 0.42rem 0;
            font-size: 0.8rem;
        }
        .cf-runtime-track {
            height: 8px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.13);
            overflow: hidden;
        }
        .cf-runtime-fill {
            height: 8px;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--cf-blue), var(--cf-cyan), var(--cf-green));
            box-shadow: 0 0 16px rgba(0, 255, 255, 0.28);
        }
        .cf-log-summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }
        .cf-log-card {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            background: rgba(10, 22, 46, 0.62);
            backdrop-filter: blur(18px);
            padding: 0.75rem;
            transition: transform 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
        }
        .cf-log-card:hover {
            transform: translateY(-4px);
            border-color: rgba(0, 255, 255, 0.34);
            box-shadow: 0 18px 44px rgba(0, 114, 255, 0.16);
        }
        .cf-log-value {
            font-size: 1.25rem;
            font-weight: 820;
            color: var(--cf-text);
        }
        .cf-log-label {
            font-size: 0.72rem;
            color: var(--cf-muted);
            text-transform: uppercase;
            font-weight: 700;
        }
        .cf-file-strip {
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            background: rgba(10, 22, 46, 0.62);
            backdrop-filter: blur(18px);
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.85rem;
            font-size: 0.82rem;
            color: var(--cf-text);
            overflow-wrap: anywhere;
        }
        .cf-file-label {
            color: var(--cf-muted);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.72rem;
            margin-right: 0.35rem;
        }
        .cf-issue-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.9rem;
        }
        .cf-issue-card {
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-left: 3px solid rgba(0, 255, 255, 0.72);
            border-radius: 16px;
            background: rgba(10, 22, 46, 0.62);
            backdrop-filter: blur(18px);
            padding: 0.9rem;
            min-height: 96px;
            box-shadow: 0 16px 42px rgba(0, 0, 0, 0.18);
            transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        }
        .cf-issue-card:hover {
            transform: translateY(-4px);
            border-color: rgba(0, 255, 255, 0.36);
            box-shadow: 0 24px 62px rgba(0, 114, 255, 0.18);
        }
        .cf-issue-title {
            color: var(--cf-text);
            font-weight: 800;
            font-size: 0.9rem;
            margin-bottom: 0.4rem;
        }
        .cf-issue-empty {
            color: var(--cf-green);
            font-size: 0.82rem;
            font-weight: 700;
        }
        .cf-issue-code {
            max-height: 160px;
            overflow: auto;
            white-space: pre-wrap;
            word-break: break-word;
            color: #dffcff;
            background: rgba(2, 8, 20, 0.72);
            border: 1px solid rgba(0, 255, 255, 0.12);
            border-radius: 12px;
            padding: 0.65rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.78rem;
        }
        .cf-table-wrap {
            width: 100%;
            overflow: auto;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 18px;
            background: rgba(2, 8, 20, 0.86);
            backdrop-filter: blur(18px);
            box-shadow: 0 18px 52px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }
        .cf-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            color: #eaf8ff;
            font-size: 0.82rem;
            min-width: 760px;
        }
        .cf-table thead th {
            position: sticky;
            top: 0;
            z-index: 2;
            text-align: left;
            color: #bdefff;
            background: linear-gradient(90deg, rgba(6, 18, 36, 0.98), rgba(15, 38, 74, 0.98));
            border-bottom: 1px solid rgba(0, 255, 255, 0.18);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            padding: 0.7rem 0.78rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .cf-table tbody td {
            color: #eaf8ff;
            background: rgba(2, 8, 20, 0.82);
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            border-right: 1px solid rgba(255, 255, 255, 0.06);
            padding: 0.68rem 0.78rem;
            white-space: nowrap;
        }
        .cf-table tbody tr:hover td {
            background: rgba(0, 255, 255, 0.1);
            color: #ffffff;
        }
        .cf-table .cf-index {
            color: #8fb5c8;
            background: rgba(6, 16, 32, 0.95);
            text-align: right;
            width: 54px;
        }
        .cf-table .cf-cell-success {
            color: #84ffd0;
            background: rgba(0, 255, 153, 0.16);
            font-weight: 800;
        }
        .cf-table .cf-cell-failed,
        .cf-table .cf-cell-error {
            color: #ffadc9;
            background: rgba(255, 61, 129, 0.2);
            font-weight: 800;
        }
        .cf-table .cf-cell-info {
            color: #8fffff;
            background: rgba(0, 255, 255, 0.12);
            font-weight: 800;
        }
        .cf-table .cf-cell-warning {
            color: #ffd88a;
            background: rgba(255, 196, 87, 0.18);
            font-weight: 800;
        }
        .cf-status-success {
            color: #047857;
            font-weight: 700;
        }
        .cf-status-failed {
            color: #b91c1c;
            font-weight: 700;
        }
        .cf-muted {
            color: var(--cf-muted);
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(0, 255, 255, 0.16);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            background: rgba(10, 22, 46, 0.68);
            backdrop-filter: blur(18px);
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.12);
            transition: transform 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-6px);
            border-color: rgba(0, 255, 255, 0.45);
            box-shadow: 0 24px 70px rgba(0, 114, 255, 0.2), 0 0 26px rgba(0, 255, 255, 0.12);
        }
        div[data-testid="stMetricLabel"] {
            color: var(--cf-muted);
            font-weight: 750;
        }
        div[data-testid="stMetricValue"] {
            color: var(--cf-text);
            font-weight: 820;
            background: linear-gradient(90deg, var(--cf-cyan), var(--cf-blue), var(--cf-green));
            background-size: 220% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: textFlow 5s linear infinite;
        }
        .stDataFrame {
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 18px;
            background: rgba(8, 16, 34, 0.78);
            backdrop-filter: blur(18px);
            box-shadow: 0 18px 52px rgba(0, 0, 0, 0.18);
            overflow: hidden;
        }
        .stDataFrame > div,
        .stDataFrame [data-testid="stDataFrameResizable"] {
            background: rgba(8, 16, 34, 0.78) !important;
        }
        .stDataFrame canvas {
            border-radius: 18px;
            filter: brightness(0.72) contrast(1.2) saturate(1.15);
        }
        div[data-testid="stAlert"] {
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            background: rgba(10, 22, 46, 0.72);
            backdrop-filter: blur(18px);
            color: var(--cf-text);
        }
        div[data-testid="stExpander"] {
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            background: rgba(10, 22, 46, 0.58);
            backdrop-filter: blur(18px);
            overflow: hidden;
        }
        div[data-testid="stExpander"] summary {
            color: var(--cf-text);
            font-weight: 700;
        }
        .stButton > button,
        .stDownloadButton > button {
            border: 0 !important;
            border-radius: 16px !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, var(--cf-blue), var(--cf-purple), var(--cf-cyan)) !important;
            box-shadow: 0 12px 34px rgba(0, 114, 255, 0.28), 0 0 18px rgba(0, 255, 255, 0.16) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease, filter 0.3s ease !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-3px);
            filter: brightness(1.1);
            box-shadow: 0 18px 48px rgba(0, 114, 255, 0.36), 0 0 28px rgba(0, 255, 255, 0.24) !important;
        }
        div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stFileUploader"] section {
            border-radius: 14px !important;
            border-color: rgba(255, 255, 255, 0.16) !important;
            background: rgba(8, 16, 34, 0.64) !important;
            color: var(--cf-text) !important;
            backdrop-filter: blur(16px);
        }
        div[data-testid="stFileUploader"] section {
            border: 1px dashed rgba(0, 255, 255, 0.28) !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }
        div[data-testid="stFileUploader"] button {
            border-radius: 12px !important;
            border: 1px solid rgba(0, 255, 255, 0.22) !important;
            color: var(--cf-text) !important;
            background: linear-gradient(135deg, rgba(0, 114, 255, 0.78), rgba(139, 92, 246, 0.78)) !important;
            box-shadow: 0 10px 28px rgba(0, 114, 255, 0.18) !important;
        }
        div[data-testid="stFileUploader"] small {
            color: var(--cf-muted) !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg {
            color: var(--cf-text) !important;
            fill: var(--cf-muted) !important;
        }
        label,
        .stCaption,
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stWidgetLabel"] {
            color: var(--cf-muted);
        }
        code,
        pre {
            border-radius: 16px !important;
            background: rgba(5, 10, 24, 0.82) !important;
            color: #dffcff !important;
            border: 1px solid rgba(0, 255, 255, 0.14) !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


def section(title, caption=None):
    st.markdown('<div class="cf-section">', unsafe_allow_html=True)
    st.markdown(f'<div class="cf-section-title">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="cf-section-caption">{caption}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def kpi_card(label, value, note=None):
    st.markdown(
        f"""
        <div class="cf-card">
            <div class="cf-card-label">{label}</div>
            <div class="cf-card-value">{value}</div>
            <div class="cf-card-note">{note or ""}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def load_history():
    history_file = "output/pipeline_history.csv"
    if not os.path.exists(history_file):
        return pd.DataFrame()
    return pd.read_csv(history_file)


def load_latest_validation_report():
    if not os.path.exists("validation_reports"):
        return None, None

    reports = [
        f for f in os.listdir("validation_reports")
        if f.endswith(".json")
    ]
    if not reports:
        return None, None

    latest = sorted(reports)[-1]
    path = os.path.join("validation_reports", latest)

    try:
        with open(path, "r") as file:
            return latest, json.load(file)
    except Exception:
        return latest, None


def load_latest_log():
    if not os.path.exists("logs"):
        return None, ""

    logs = [
        f for f in os.listdir("logs")
        if f.endswith(".log")
    ]
    if not logs:
        return None, ""

    latest = sorted(logs)[-1]
    path = os.path.join("logs", latest)

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            lines = file.readlines()
        return latest, "".join(lines[-250:])
    except Exception as exc:
        return latest, f"Could not load log file: {exc}"


def parse_log_text(log_text):
    rows = []

    for line in log_text.splitlines():
        parts = [part.strip() for part in line.split("|", 2)]
        if len(parts) == 3:
            rows.append({
                "timestamp": parts[0],
                "level": parts[1],
                "message": parts[2]
            })
        elif line.strip():
            rows.append({
                "timestamp": "",
                "level": "DETAIL",
                "message": line.strip()
            })

    return pd.DataFrame(rows)


def style_glass_table(df):
    if df.empty:
        return df

    return (
        df.style
        .set_properties(**{
            "background-color": "#071225",
            "color": "#eaf8ff",
            "border-color": "rgba(255, 255, 255, 0.08)"
        })
        .set_table_styles([
            {
                "selector": "thead th",
                "props": [
                    ("background", "linear-gradient(90deg, #071225, #10254a)"),
                    ("color", "#bdefff"),
                    ("font-weight", "800"),
                    ("border-color", "rgba(0, 255, 255, 0.18)")
                ]
            },
            {
                "selector": "tbody tr:hover td",
                "props": [
                    ("background-color", "rgba(0, 255, 255, 0.12)"),
                    ("color", "#ffffff")
                ]
            },
            {
                "selector": "tbody th",
                "props": [
                    ("background-color", "#06101f"),
                    ("color", "#8fb5c8"),
                    ("border-color", "rgba(255, 255, 255, 0.08)")
                ]
            }
        ])
    )


def render_glass_table(df, height=360):
    if df.empty:
        st.info("No rows to display.")
        return

    headers = ['<th class="cf-index"></th>']
    for column in df.columns:
        headers.append(f"<th>{html.escape(str(column))}</th>")

    body_rows = []
    for index, row in df.iterrows():
        cells = [f'<td class="cf-index">{html.escape(str(index))}</td>']

        for column in df.columns:
            value = row[column]
            normalized = str(value).strip().lower()
            cell_class = ""

            if normalized == "success":
                cell_class = "cf-cell-success"
            elif normalized == "failed":
                cell_class = "cf-cell-failed"
            elif normalized == "error":
                cell_class = "cf-cell-error"
            elif normalized == "warning":
                cell_class = "cf-cell-warning"
            elif normalized == "info":
                cell_class = "cf-cell-info"

            cells.append(
                f'<td class="{cell_class}">{html.escape(str(value))}</td>'
            )

        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_html = (
        f'<div class="cf-table-wrap" style="max-height:{height}px;">'
        '<table class="cf-table">'
        f"<thead><tr>{''.join(headers)}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
    )

    st.markdown(table_html, unsafe_allow_html=True)


def render_issue_cards(failure_blocks):
    cards = []

    for label, value in failure_blocks.items():
        has_value = bool(value)
        if has_value:
            rendered_value = html.escape(json.dumps(value, indent=2, default=str))
            content = f'<div class="cf-issue-code">{rendered_value}</div>'
        else:
            content = '<div class="cf-issue-empty">No issues detected</div>'

        cards.append(
            '<div class="cf-issue-card">'
            f'<div class="cf-issue-title">{html.escape(label)}</div>'
            f'{content}'
            '</div>'
        )

    st.markdown(
        f'<div class="cf-issue-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True
    )


def style_log_table(df):
    if df.empty or "level" not in df.columns:
        return style_glass_table(df)

    def color_level(row):
        level = str(row.get("level", "")).upper()
        if level == "ERROR":
            color = "background-color: rgba(255, 61, 129, 0.22); color: #ffb1cc"
        elif level == "WARNING":
            color = "background-color: rgba(255, 196, 87, 0.18); color: #ffd88a"
        elif level == "INFO":
            color = "background-color: rgba(0, 255, 255, 0.12); color: #8fffff"
        else:
            color = "background-color: rgba(255, 255, 255, 0.06); color: #c7d2e1"

        return [color if col == "level" else "" for col in row.index]

    return style_glass_table(df).apply(color_level, axis=1)


def render_status_distribution(successful, failed, total):
    success_width = round((successful / total * 100), 1) if total else 0
    failed_width = round((failed / total * 100), 1) if total else 0

    st.markdown(
        f"""
        <div class="cf-panel">
            <div class="cf-panel-title">Status Distribution</div>
            <div class="cf-panel-caption">Compact pass/fail split for the selected run set.</div>
            <span class="cf-pill cf-pill-success">Success {success_width:.1f}%</span>
            <span class="cf-pill cf-pill-failed">Failed {failed_width:.1f}%</span>
            <div class="cf-bar-track">
                <div class="cf-bar-success" style="width:{success_width}%;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:0.8rem; color:#6b7280; font-size:0.8rem;">
                <span>{successful} successful</span>
                <span>{failed} failed</span>
                <span>{total} total</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_runtime_summary(df):
    if df.empty or "execution_time_sec" not in df.columns:
        st.info("Execution time is not available in history.")
        return

    runtimes = df["execution_time_sec"].fillna(0).tail(8).reset_index(drop=True)
    max_runtime = max(float(runtimes.max()), 1.0)
    latest_runtime = float(runtimes.iloc[-1]) if len(runtimes) else 0
    avg_runtime = float(runtimes.mean()) if len(runtimes) else 0

    rows = ""
    for idx, value in enumerate(runtimes, start=1):
        width = min(100, round(float(value) / max_runtime * 100, 1))
        rows += (
            f'<div class="cf-runtime-row">'
            f'<div>Run {idx}</div>'
            f'<div class="cf-runtime-track">'
            f'<div class="cf-runtime-fill" style="width:{width}%;"></div>'
            f'</div>'
            f'<div>{float(value):.2f}s</div>'
            f'</div>'
        )

    st.markdown(
        (
            '<div class="cf-panel">'
            '<div class="cf-panel-title">Execution Time</div>'
            '<div class="cf-panel-caption">'
            'Recent runtimes shown as comparable bars instead of sparse charts.'
            '</div>'
            '<div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem; margin-bottom:0.8rem;">'
            '<div>'
            '<div class="cf-card-label">Latest</div>'
            f'<div class="cf-card-value">{latest_runtime:.2f}s</div>'
            '</div>'
            '<div>'
            '<div class="cf-card-label">Average</div>'
            f'<div class="cf-card-value">{avg_runtime:.2f}s</div>'
            '</div>'
            '</div>'
            f'{rows}'
            '</div>'
        ),
        unsafe_allow_html=True
    )


def style_history_table(df):
    if df.empty or "status" not in df.columns:
        return style_glass_table(df)

    def color_status(row):
        status = str(row.get("status", "")).lower()
        if status == "success":
            return ["background-color: rgba(0, 255, 153, 0.18); color: #8affd0" if col == "status" else "" for col in row.index]
        if status == "failed":
            return ["background-color: rgba(255, 61, 129, 0.2); color: #ffadc9" if col == "status" else "" for col in row.index]
        return ["" for _ in row.index]

    return style_glass_table(df).apply(color_status, axis=1)


st.markdown(
    """
    <div class="cf-header">
        <div class="cf-title">CloudForge Data Intelligence Platform</div>
        <div class="cf-subtitle">
            Production pipeline operations, data quality, lineage signals, and run history.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

history_df = load_history()
output_files = [
    f for f in os.listdir("output")
    if f.startswith("processed_")
] if os.path.exists("output") else []

total_runs = len(history_df) if not history_df.empty else 0
successful_runs = (
    len(history_df[history_df["status"] == "success"])
    if not history_df.empty and "status" in history_df.columns
    else 0
)
failed_runs = (
    len(history_df[history_df["status"] == "failed"])
    if not history_df.empty and "status" in history_df.columns
    else 0
)
success_rate = (successful_runs / total_runs * 100) if total_runs else 0
avg_time = (
    history_df["execution_time_sec"].mean()
    if not history_df.empty and "execution_time_sec" in history_df.columns
    else 0
)

section(
    "Overview KPIs",
    "High-signal operational metrics for recent CloudForge pipeline activity."
)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    kpi_card("Success Rate", f"{success_rate:.1f}%", f"{successful_runs} successful runs")
with k2:
    kpi_card("Failures", failed_runs, "Runs requiring review")
with k3:
    kpi_card("Total Runs", total_runs, "Tracked executions")
with k4:
    kpi_card("Avg Runtime", f"{avg_time:.2f}s", "Mean execution time")
with k5:
    kpi_card("Processed Files", len(output_files), "Available outputs")


with st.sidebar:
    st.markdown("### Pipeline Control")

    source_type = st.selectbox(
        "Data source",
        [
            "CSV File",
            "Excel File (.xlsx / .xls)",
            "JSON File",
            "Parquet File",
            "SQLite Database",
            "MySQL Database",
            "PostgreSQL Database"
        ]
    )

    output_format = st.selectbox(
        "Output format",
        ["csv", "parquet"]
    )

    source = None
    source_key = None
    extra_kwargs = {}

    if source_type == "CSV File":
        uploaded = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded:
            save_path = f"data/{uploaded.name}"
            os.makedirs("data", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            source = save_path
            source_key = "csv"
            st.success(f"Ready: {save_path}")

    elif source_type == "Excel File (.xlsx / .xls)":
        uploaded = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
        if uploaded:
            save_path = f"data/{uploaded.name}"
            os.makedirs("data", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            source = save_path
            source_key = "xlsx"
            sheet = st.text_input("Sheet name", value="")
            if sheet:
                extra_kwargs["sheet_name"] = sheet
            st.success(f"Ready: {save_path}")

    elif source_type == "JSON File":
        uploaded = st.file_uploader("Upload JSON file", type=["json"])
        if uploaded:
            save_path = f"data/{uploaded.name}"
            os.makedirs("data", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            source = save_path
            source_key = "json"
            st.success(f"Ready: {save_path}")

    elif source_type == "Parquet File":
        uploaded = st.file_uploader("Upload Parquet file", type=["parquet"])
        if uploaded:
            save_path = f"data/{uploaded.name}"
            os.makedirs("data", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            source = save_path
            source_key = "parquet"
            st.success(f"Ready: {save_path}")

    elif source_type == "SQLite Database":
        uploaded = st.file_uploader("Upload SQLite file", type=["db", "sqlite", "sqlite3"])
        if uploaded:
            save_path = f"data/{uploaded.name}"
            os.makedirs("data", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            source = save_path
            source_key = "sqlite"
            table_name = st.text_input("Table name")
            sql_query = st.text_area("SQL query")
            if table_name:
                extra_kwargs["table"] = table_name
            if sql_query:
                extra_kwargs["query"] = sql_query
            st.success(f"Ready: {save_path}")

    elif source_type == "MySQL Database":
        conn_str = st.text_input("Connection string")
        table_name = st.text_input("Table name")
        sql_query = st.text_area("SQL query")
        if conn_str:
            source = conn_str
            source_key = "mysql"
            if table_name:
                extra_kwargs["table"] = table_name
            if sql_query:
                extra_kwargs["query"] = sql_query

    elif source_type == "PostgreSQL Database":
        conn_str = st.text_input("Connection string")
        table_name = st.text_input("Table name")
        sql_query = st.text_area("SQL query")
        if conn_str:
            source = conn_str
            source_key = "postgresql"
            if table_name:
                extra_kwargs["table"] = table_name
            if sql_query:
                extra_kwargs["query"] = sql_query

    run_clicked = st.button("Execute Pipeline", type="primary", use_container_width=True)


section(
    "Pipeline Execution",
    "Run CloudForge with the selected source configuration."
)

if run_clicked:
    if not source:
        st.error("Provide a data source before executing the pipeline.")
    else:
        start_time = time.time()

        with st.spinner("Running CloudForge pipeline..."):
            try:
                result = pipeline.run_pipeline(
                    source=source,
                    source_type=source_key,
                    output_format=output_format,
                    **extra_kwargs
                )

                execution_time = time.time() - start_time
                log_pipeline_run(result, execution_time)

                if result.get("status") == "success":
                    st.success("Pipeline completed successfully.")

                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Rows Processed", f"{result.get('rows_processed', 0):,}")
                    r2.metric("Source Type", str(result.get("source_type", "")).upper())
                    r3.metric("Output Format", str(result.get("output_format", "")).upper())
                    r4.metric("Execution Time", f"{execution_time:.2f}s")

                    with st.expander("Run Result", expanded=False):
                        st.json(result)

                    if result.get("output_file"):
                        s3_uri = s3.upload_file(result["output_file"], "processed")
                        st.info(f"Processed artifact uploaded: {s3_uri}")
                else:
                    st.error(
                        f"Pipeline failed at {result.get('stage', 'unknown')} "
                        f"with reason: {result.get('reason', 'unknown')}"
                    )
                    with st.expander("Failure Details", expanded=True):
                        st.json(result)

            except Exception as e:
                execution_time = time.time() - start_time
                st.error(f"Pipeline error: {str(e)}")
                log_pipeline_run(
                    {"status": "failed", "rows_processed": 0, "output_file": ""},
                    execution_time
                )
else:
    st.info("Configure a source in the sidebar, then execute the pipeline.")


section(
    "Pipeline Runs History",
    "Filter and inspect pipeline executions with status-aware table formatting."
)

if history_df.empty:
    st.info("No pipeline history yet.")
else:
    f1, f2, f3 = st.columns([1, 1, 2])

    with f1:
        status_options = ["All"] + sorted(history_df["status"].dropna().unique().tolist())
        status_filter = st.selectbox("Status", status_options)

    with f2:
        if "source_type" in history_df.columns:
            source_options = ["All"] + sorted(history_df["source_type"].dropna().unique().tolist())
        else:
            source_options = ["All"]
        source_filter = st.selectbox("Source type", source_options)

    with f3:
        st.caption("The table below preserves the existing history data while improving scanability.")

    filtered = history_df.copy()
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]
    if source_filter != "All" and "source_type" in filtered.columns:
        filtered = filtered[filtered["source_type"] == source_filter]

    table_columns = [
        col for col in [
            "run_id",
            "timestamp",
            "status",
            "source_type",
            "rows_processed",
            "execution_time_sec",
            "output_file"
        ]
        if col in filtered.columns
    ]

    render_glass_table(
        filtered[table_columns] if table_columns else filtered,
        height=360
    )

    csv_export = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download History CSV",
        data=csv_export,
        file_name="pipeline_history.csv",
        mime="text/csv"
    )

    if len(filtered) > 0:
        chart_left, chart_right = st.columns(2)

        with chart_left:
            render_runtime_summary(filtered)

        with chart_right:
            if "status" in filtered.columns:
                selected_total = len(filtered)
                selected_success = len(filtered[filtered["status"] == "success"])
                selected_failed = len(filtered[filtered["status"] == "failed"])
                render_status_distribution(
                    successful=selected_success,
                    failed=selected_failed,
                    total=selected_total
                )
            else:
                st.info("Status data is not available in history.")


section(
    "Validation Failures",
    "Latest validation report with focused failure indicators."
)

report_name, validation_report = load_latest_validation_report()
if not report_name:
    st.info("No validation reports found.")
elif validation_report is None:
    st.warning(f"Could not parse validation report: {report_name}")
else:
    validation_status = validation_report.get("status")
    if validation_status is None:
        validation_status = (
            "success"
            if validation_report.get("overall_validation_status") is True
            else "failed"
        )

    st.markdown(
        f"""
        <div class="cf-file-strip">
            <span class="cf-file-label">Report</span>{report_name}
        </div>
        """,
        unsafe_allow_html=True
    )

    v1, v2, v3 = st.columns(3)
    v1.metric("Rows", validation_report.get("row_count", 0))
    v2.metric("Duplicate Rows", validation_report.get("duplicate_rows", 0))
    v3.metric("Status", str(validation_status).upper())

    failure_blocks = {
        "Missing Columns": validation_report.get("missing_columns", []),
        "Extra Columns": validation_report.get("extra_columns", []),
        "Datatype Issues": validation_report.get("datatype_issues", {}),
        "Business Rule Failures": validation_report.get("business_rule_failures", {})
    }

    render_issue_cards(failure_blocks)


section(
    "Data Quality Insights",
    "Preview the latest processed dataset and summarize its shape."
)

if output_files:
    latest = sorted(output_files)[-1]
    path = os.path.join("output", latest)

    try:
        if latest.endswith(".parquet"):
            preview_df = pd.read_parquet(path)
        else:
            preview_df = pd.read_csv(path)

        p1, p2, p3 = st.columns(3)
        p1.metric("Rows", f"{preview_df.shape[0]:,}")
        p2.metric("Columns", preview_df.shape[1])
        p3.metric("Format", "Parquet" if latest.endswith(".parquet") else "CSV")

        st.caption(f"Latest artifact: {latest}")
        render_glass_table(preview_df.head(100), height=360)

    except Exception as e:
        st.error(f"Could not load latest processed dataset: {e}")
else:
    st.info("No processed datasets found.")


section(
    "Storage Snapshot",
    "Read-only view of current S3 layer contents."
)

try:
    files = s3.list_bucket_files()
    if files:
        st.metric("S3 Objects", len(files))
        render_glass_table(pd.DataFrame({"s3_key": files}), height=260)
    else:
        st.info("S3 bucket is empty.")
except Exception as e:
    st.error(f"S3 error: {str(e)}")


section(
    "Execution Logs",
    "Most recent log lines for operational debugging."
)

log_name, log_text = load_latest_log()
if not log_name:
    st.info("No log files found.")
else:
    st.caption(f"Latest log: {log_name}")
    log_df = parse_log_text(log_text)

    if log_df.empty:
        st.info("Log file is empty.")
    else:
        info_count = len(log_df[log_df["level"].str.upper() == "INFO"])
        warning_count = len(log_df[log_df["level"].str.upper() == "WARNING"])
        error_count = len(log_df[log_df["level"].str.upper() == "ERROR"])

        st.markdown(
            f"""
            <div class="cf-log-summary">
                <div class="cf-log-card">
                    <div class="cf-log-label">Visible Events</div>
                    <div class="cf-log-value">{len(log_df)}</div>
                </div>
                <div class="cf-log-card">
                    <div class="cf-log-label">Info</div>
                    <div class="cf-log-value">{info_count}</div>
                </div>
                <div class="cf-log-card">
                    <div class="cf-log-label">Warnings</div>
                    <div class="cf-log-value">{warning_count}</div>
                </div>
                <div class="cf-log-card">
                    <div class="cf-log-label">Errors</div>
                    <div class="cf-log-value">{error_count}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        log_levels = ["All"] + sorted(log_df["level"].dropna().unique().tolist())
        selected_level = st.selectbox("Log level", log_levels)

        filtered_logs = log_df.copy()
        if selected_level != "All":
            filtered_logs = filtered_logs[filtered_logs["level"] == selected_level]

        render_glass_table(filtered_logs.tail(80), height=360)

        with st.expander("Raw log tail", expanded=False):
            st.code(log_text or "Log file is empty.", language="text")
