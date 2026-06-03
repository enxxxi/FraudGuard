import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import random
import textwrap
from urllib import error, parse, request


# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================
st.set_page_config(page_title="FraudGuard - Fraud Detection Dashboard", layout="wide", initial_sidebar_state="expanded")

# Handle query parameters for page navigation
params = {}
try:
    params = st.query_params
except AttributeError:
    try:
        experimental_get = getattr(st, "experimental_get_query_params", None)
        if experimental_get is not None:
            params = experimental_get()
    except Exception:
        pass

if "page" in params:
    nav_page = params["page"]
    if isinstance(nav_page, list):
        nav_page = nav_page[0] if nav_page else ""
    valid_pages = ["Dashboard", "Email Inbox", "Transactions", "Analytics"]
    if nav_page in valid_pages:
        st.session_state.nav_radio = nav_page

if "email_idx" in params:
    try:
        idx_val = params["email_idx"]
        if isinstance(idx_val, list):
            idx_val = idx_val[0] if idx_val else "0"
        st.session_state.selected_email_idx = int(idx_val)
    except Exception:
        pass

if "page" in params or "email_idx" in params:
    try:
        st.query_params.clear()
    except AttributeError:
        try:
            experimental_set = getattr(st, "experimental_set_query_params", None)
            if experimental_set is not None:
                experimental_set()
        except Exception:
            pass

# Custom CSS to mirror reference dashboard design
st.markdown("""
<style>
    :root {
        --bg: #eef2f6;
        --surface: #ffffff;
        --text: #0f2a47;
        --muted: #6b7b92;
        --primary: #132a46;
        --border: #d9e0e8;
        --shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
        --radius: 14px;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }

    [data-testid="collapsedControl"] {
        display: none !important;
        position: fixed;
        top: 0.8rem;
        left: 0.8rem;
        z-index: 999999;
        background: #ffffff;
        border: 1px solid #d9e0e8;
        border-radius: 8px;
        width: 38px !important;
        height: 38px !important;
        padding: 0 !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
    }

    [data-testid="collapsedControl"] button {
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        color: #0f2a47 !important;
        font-size: 1.3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        padding: 0 !important;
    }

    [data-testid="collapsedControl"] button:hover {
        background: #f5f8fb !important;
    }

    .block-container {
        max-width: none;
        padding: 0 1.9rem 1.25rem;
    }

    div[data-testid="stMarkdownContainer"] .inbox-shell {
        max-width: 100%;
    }

    @media (max-width: 960px) {
        .inbox-shell {
            grid-template-columns: 1fr;
        }

        .mail-list {
            max-height: 320px;
            border-right: 0;
            border-bottom: 1px solid #d7e0ea;
        }
    }

    section[data-testid="stSidebar"][aria-expanded="true"],
    [data-testid="stSidebar"][aria-expanded="true"] {
        background: #1c2a3a;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        width: 250px !important;
        min-width: 250px !important;
        max-width: 250px !important;
    }

    section[data-testid="stSidebar"][aria-expanded="true"] > div,
    [data-testid="stSidebar"][aria-expanded="true"] > div {
        width: 250px !important;
    }

    section[data-testid="stSidebar"][aria-expanded="false"],
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        border-right: 0 !important;
    }

    section[data-testid="stSidebar"][aria-expanded="false"] > div,
    [data-testid="stSidebar"][aria-expanded="false"] > div {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }

    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    [data-testid="stSidebar"] * {
        color: #eef4ff;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        margin-bottom: 0;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0 0.6rem 0.85rem;
        margin-top: -3.1rem;
        margin-bottom: 0.65rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    }

    .brand-mark {
        width: 44px;
        height: 44px;
        border-radius: 8px;
        background: #2d3c51;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
    }

    .brand-title {
        color: #ffffff;
        font-size: 1.35rem;
        line-height: 1.05;
        font-weight: 800;
    }

    .brand-subtitle {
        color: #9baabe;
        font-size: 0.72rem;
        line-height: 1.1;
        margin-top: 0.35rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 600;
    }

    .sidebar-section-label {
        color: #b9c6d8;
        font-size: 0.88rem;
        font-weight: 800;
        padding: 0 0.6rem;
        margin-bottom: 0.45rem;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 0.12rem;
        width: 100%;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        min-height: 40px;
        width: 100%;
        border-radius: 7px;
        padding: 0.42rem 0.7rem;
        margin: 0;
        transition: background 120ms ease;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(45, 60, 81, 0.68);
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: #2d3c51;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #f8fbff;
        font-size: 1.02rem;
        font-weight: 700;
        line-height: 1.2;
        display: flex;
        align-items: center;
        gap: 0.65rem;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label p::before {
        content: "";
        width: 20px;
        height: 20px;
        flex: 0 0 20px;
        background-color: #dfe8f4;
        -webkit-mask-position: center;
        -webkit-mask-repeat: no-repeat;
        -webkit-mask-size: contain;
        mask-position: center;
        mask-repeat: no-repeat;
        mask-size: contain;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:nth-child(1) p::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M4%204h6v6H4V4Zm10%200h6v6h-6V4ZM4%2014h6v6H4v-6Zm10%200h6v6h-6v-6Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M4%204h6v6H4V4Zm10%200h6v6h-6V4ZM4%2014h6v6H4v-6Zm10%200h6v6h-6v-6Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:nth-child(2) p::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M3%206h18v12H3V6Zm9%207L3%207v2l9%207%209-7V7l-9%206Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M3%206h18v12H3V6Zm9%207L3%207v2l9%207%209-7V7l-9%206Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:nth-child(3) p::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M4%204h16v16H4V4Zm9%203h-2v2c-1.8.3-3%201.4-3%202.8%200%201.7%201.4%202.5%203.7%203%201.3.3%201.8.6%201.8%201.2%200%20.7-.7%201.1-1.8%201.1-1.2%200-2.3-.5-3.1-1.3L7%2016c.9%201%202.3%201.7%204%201.8V20h2v-2.3c1.8-.3%203-1.5%203-3%200-1.8-1.5-2.6-3.8-3.1-1.2-.3-1.8-.6-1.8-1.1%200-.6.6-1%201.5-1%201%200%201.8.3%202.5%201l1.2-1.6c-.7-.8-1.6-1.3-2.6-1.5V7Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M4%204h16v16H4V4Zm9%203h-2v2c-1.8.3-3%201.4-3%202.8%200%201.7%201.4%202.5%203.7%203%201.3.3%201.8.6%201.8%201.2%200%20.7-.7%201.1-1.8%201.1-1.2%200-2.3-.5-3.1-1.3L7%2016c.9%201%202.3%201.7%204%201.8V20h2v-2.3c1.8-.3%203-1.5%203-3%200-1.8-1.5-2.6-3.8-3.1-1.2-.3-1.8-.6-1.8-1.1%200-.6.6-1%201.5-1%201%200%201.8.3%202.5%201l1.2-1.6c-.7-.8-1.6-1.3-2.6-1.5V7Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:nth-child(4) p::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M4%203h2v16h15v2H4V3Zm5%2013V9h2v7H9Zm5%200V5h2v11h-2Zm5%200V8h2v8h-2Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg%20viewBox%3D%270%200%2024%2024%27%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%3E%3Cpath%20d%3D%27M4%203h2v16h15v2H4V3Zm5%2013V9h2v7H9Zm5%200V5h2v11h-2Zm5%200V8h2v8h-2Z%27%20fill%3D%27black%27/%3E%3C/svg%3E");
    }

    .hero-title {
        color: #0f2a47;
        font-size: 2.25rem;
        line-height: 1.1;
        letter-spacing: 0;
        margin: 1.9rem 0 0.35rem;
        font-weight: 700;
    }

    .hero-sub {
        color: var(--muted);
        margin-bottom: 1.65rem;
        font-size: 1.05rem;
    }

    .kpi-card {
        position: relative;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.45rem 1.6rem;
        box-shadow: var(--shadow);
        min-height: 152px;
    }

    .kpi-icon {
        position: absolute;
        top: 1.55rem;
        right: 1.55rem;
        width: 50px;
        height: 50px;
        border-radius: 8px;
        background: #eef3f8;
        color: #0f2a47;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    .kpi-icon svg {
        width: 24px;
        height: 24px;
    }

    .kpi-title {
        color: var(--muted);
        text-transform: uppercase;
        font-size: 0.82rem;
        letter-spacing: 0.18em;
        margin-bottom: 1.05rem;
        font-weight: 700;
    }

    .kpi-value {
        font-size: 2.35rem;
        color: #0f2a47;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.7rem;
    }

    .kpi-sub {
        color: var(--muted);
        margin-top: 0.15rem;
        font-size: 0.9rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        box-shadow: var(--shadow);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 1.45rem 1.8rem 1.2rem;
    }

    .stButton > button {
        min-height: 40px;
        height: 40px;
        border-radius: 7px;
        border: 1px solid #cfd7e3;
        padding: 0.35rem 0.95rem;
        font-weight: 700;
        font-size: 0.55rem;
        background: #ffffff;
        color: #1b2b44;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .stButton > button[kind="primary"] {
        background: #243851;
        color: #ffffff;
        border: 1px solid #243851;
    }

    .top-strip {
        background: #ffffff;
        border-bottom: 1px solid #d8e1eb;
        border-radius: 0;
        padding: 0 1.9rem;
        height: 68px;
        margin: 0 -1.9rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .top-strip-left {
        color: #1b2b44;
        font-size: 1.05rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.65rem;
    }

    .top-strip-left span {
        color: #8a97ab;
        font-size: 0.95rem;
        font-weight: 500;
        margin-left: 0;
    }

    .top-strip-right {
        color: #3f5773;
        font-weight: 600;
        font-size: 0.92rem;
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 0;
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
    }

    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: #38b16a;
        box-shadow: 0 0 0 5px rgba(56, 177, 106, 0.15);
    }

    .chart-title {
        color: #071f3d;
        font-size: 1.25rem;
        font-weight: 800;
        line-height: 1.2;
        margin: 0 0 1rem;
    }

    .page-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        padding: 2rem 0 1.65rem;
    }

    .page-title {
        color: #071f3d;
        font-size: 2.25rem;
        line-height: 1.05;
        font-weight: 800;
        margin-bottom: 0.55rem;
    }

    .page-subtitle {
        color: #465a72;
        font-size: 1rem;
        line-height: 1.4;
    }

    .page-actions {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding-top: 0.15rem;
    }

    .action-btn {
        min-width: 142px;
        height: 40px;
        border-radius: 7px;
        border: 1px solid #cfd7e3;
        background: #ffffff;
        color: #071f3d;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.55rem;
        font-size: 0.78rem;
        font-weight: 800;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
        white-space: nowrap;
    }

    .action-btn-danger {
        min-width: 186px;
        background: #e7283b;
        border-color: #e7283b;
        color: #ffffff;
    }

    .inbox-shell {
        display: grid;
        grid-template-columns: minmax(260px, 34%) minmax(320px, 1fr);
        min-height: 680px;
        margin: 0 -1.9rem -1.25rem;
        border-top: 1px solid #d7e0ea;
        background: #f6f9fc;
        width: 100%;
    }

    .mail-list {
        background: #f8fafc;
        border-right: 1px solid #d7e0ea;
        max-height: 680px;
        overflow-y: auto;
        min-width: 0;
    }

    .mail-item {
        padding: 1.35rem 1.25rem 1.25rem;
        border-bottom: 1px solid #d7e0ea;
        background: #f8fafc;
        cursor: pointer;
        transition: background 150ms ease;
    }

    .mail-item:hover {
        background: #eaeff4 !important;
    }

    .mail-item-active {
        background: #dce7ef !important;
    }

    .mail-row {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .mail-sender {
        color: #4b5c73;
        font-size: 0.84rem;
        font-weight: 700;
        min-width: 0;
        flex: 1 1 auto;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .risk-pill {
        min-width: 66px;
        height: 26px;
        border-radius: 7px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.78rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        flex: 0 0 auto;
    }

    .risk-high {
        color: #e7283b;
        border: 1px solid #e7283b;
        background: #ffffff;
    }

    .risk-medium {
        color: #d99200;
        border: 1px solid #e6a000;
        background: #fffaf0;
    }

    .risk-low {
        color: #159553;
        border: 1px solid #159553;
        background: #f7fffb;
    }

    .mail-subject {
        color: #001a39;
        font-size: 0.98rem;
        font-weight: 850;
        line-height: 1.3;
        margin-bottom: 0.55rem;
    }

    .mail-preview,
    .mail-time {
        color: #4b5c73;
        font-size: 0.83rem;
        line-height: 1.45;
    }

    .mail-detail {
        padding: 1.5rem 1.5rem 2rem;
        background: #f6f9fc;
        min-width: 0;
        overflow-x: hidden;
        overflow-y: auto;
    }

    .email-card,
    .analysis-card {
        background: #ffffff;
        border: 1px solid #d7e0ea;
        border-radius: 13px;
        box-shadow: var(--shadow);
    }

    .email-card {
        margin-bottom: 1.85rem;
    }

    .email-head {
        display: flex;
        gap: 1rem;
        align-items: center;
        padding: 1.9rem 1.8rem 1.65rem;
        border-bottom: 1px solid #d7e0ea;
    }

    .email-icon {
        width: 50px;
        height: 50px;
        border-radius: 7px;
        background: #2d3c51;
        color: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
    }

    .email-subject {
        color: #001a39;
        font-size: 1.45rem;
        line-height: 1.15;
        font-weight: 850;
        margin-bottom: 0.45rem;
    }

    .email-meta {
        color: #4b5c73;
        font-size: 0.9rem;
    }

    .email-body {
        color: #001a39;
        font-size: 1.02rem;
        line-height: 1.55;
        padding: 2rem 1.8rem;
    }

    .analysis-card {
        border-color: #f0c86e;
        padding: 1.9rem 1.8rem;
    }

    .analysis-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 2.1rem;
    }

    .analysis-title {
        color: #071f3d;
        font-size: 1.25rem;
        font-weight: 850;
    }

    .risk-solid {
        min-width: 108px;
        height: 30px;
        border-radius: 7px;
        color: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.78rem;
        font-weight: 900;
        flex: 0 0 auto;
        white-space: nowrap;
    }

    .risk-solid-high { background: #e7283b; }
    .risk-solid-medium { background: #e39a00; }
    .risk-solid-low { background: #35a165; }

    .prob-row {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }

    .prob-label,
    .reason-label,
    .detail-label {
        color: #5b6c82;
        font-size: 0.77rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 700;
        white-space: normal;
        word-break: break-word;
    }

    .prob-value {
        color: #e39a00;
        font-size: 2.1rem;
        line-height: 1;
        font-weight: 850;
    }

    .prob-track {
        height: 10px;
        border-radius: 999px;
        background: #e9eef3;
        overflow: hidden;
        margin-bottom: 1.6rem;
    }

    .prob-fill {
        height: 100%;
        border-radius: 999px;
        background: #e39a00;
    }

    .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.8rem;
        margin-bottom: 1.55rem;
    }

    .detail-box {
        border: 1px solid #d7e0ea;
        border-radius: 7px;
        padding: 0.9rem 0.95rem;
        background: #fbfcfe;
    }

    .detail-value {
        color: #001a39;
        font-size: 0.96rem;
        font-weight: 850;
        margin-top: 0.5rem;
    }

    .reason-list {
        margin: 0.7rem 0 0;
        color: #001a39;
        font-size: 0.98rem;
        line-height: 1.65;
    }

    .reason-list ul {
        margin: 0.35rem 0 0.75rem;
        padding-left: 1.2rem;
    }

    .reason-list li::marker {
        color: #e39a00;
    }

    .tx-controls {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin: 0 0 1.8rem;
    }

    .tx-search {
        height: 46px;
        flex: 1;
        border: 1px solid #d7e0ea;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: var(--shadow);
        color: #5b6c82;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0 1rem;
        font-size: 0.96rem;
    }

    .tx-filter {
        height: 40px;
        min-width: 70px;
        border-radius: 7px;
        border: 1px solid #d7e0ea;
        background: #ffffff;
        color: #071f3d;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.78rem;
        font-weight: 850;
        box-shadow: var(--shadow);
    }

    .tx-filter-active {
        background: #243851;
        border-color: #243851;
        color: #ffffff;
    }

    .tx-table-card {
        background: #ffffff;
        border: 1px solid #d7e0ea;
        border-radius: 13px;
        box-shadow: var(--shadow);
        overflow: hidden;
    }

    .tx-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }

    .tx-table th {
        background: #fbfcfe;
        color: #4e5d73;
        font-size: 0.78rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        text-align: left;
        font-weight: 850;
        padding: 1rem 1.25rem;
        border-bottom: 1px solid #d7e0ea;
    }

    .tx-table td {
        color: #071f3d;
        font-size: 0.96rem;
        padding: 0.86rem 1.25rem;
        border-bottom: 1px solid #d7e0ea;
        vertical-align: middle;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .tx-table tr:nth-child(8) td {
        background: #f2f5f8;
    }

    .tx-table tr:last-child td {
        border-bottom: 0;
    }

    .tx-time {
        font-family: monospace;
        color: #203a59;
        font-size: 0.9rem;
    }

    .tx-merchant {
        font-weight: 850;
        color: #001a39;
    }

    .tx-muted {
        color: #465a72;
    }

    .tx-amount {
        text-align: right;
        font-family: monospace;
        color: #001a39;
        font-size: 0.98rem;
    }

    .tx-prob {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .tx-prob-track {
        width: 82px;
        height: 7px;
        border-radius: 999px;
        background: #e9eef3;
        overflow: hidden;
    }

    .tx-prob-fill {
        height: 100%;
        border-radius: 999px;
    }

    .tx-prob-text {
        font-size: 0.82rem;
        font-family: monospace;
    }

    .analytics-legend {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-top: -0.5rem;
        color: #001a39;
        font-family: monospace;
        font-size: 0.9rem;
    }

    .legend-dot {
        width: 15px;
        height: 15px;
        border-radius: 4px;
        display: inline-block;
        margin-right: 0.45rem;
        vertical-align: -2px;
    }

    .summary-row {
        margin-bottom: 1.05rem;
    }

    .summary-line {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 0.4rem;
    }

    .summary-name {
        color: #001a39;
        font-size: 0.96rem;
        font-weight: 850;
    }

    .summary-meta {
        color: #263a55;
        font-family: monospace;
        font-size: 0.95rem;
        white-space: nowrap;
    }

    .summary-track {
        height: 7px;
        border-radius: 999px;
        background: #e9eef3;
        overflow: hidden;
    }

    .summary-fill {
        height: 100%;
        border-radius: 999px;
        background: #e7283b;
    }

    /* Inbox Column Styles */
    div[data-testid="stHorizontalBlock"]:has(div.mail-item) {
        background: #f6f9fc !important;
        border-top: 1px solid #d7e0ea !important;
        margin: 0 -1.9rem -1.25rem !important;
        min-height: 680px !important;
        gap: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(div.mail-item) > div[data-testid="column"]:first-child {
        background: #f8fafc !important;
        border-right: 1px solid #d7e0ea !important;
        max-height: 680px !important;
        overflow-y: auto !important;
        padding: 0 !important;
        flex: 0 0 34% !important;
        max-width: 34% !important;
        min-width: 260px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(div.mail-item) > div[data-testid="column"]:last-child {
        padding: 1.5rem !important;
        flex: 1 1 auto !important;
        max-width: 66% !important;
        background: #f6f9fc !important;
        overflow-y: auto !important;
        max-height: 680px !important;
    }

    /* Hide the hidden text input container */
    div[data-testid="element-container"]:has(input[aria-label="selected_email_idx_hidden"]),
    div[data-testid="stElementContainer"]:has(input[aria-label="selected_email_idx_hidden"]) {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar branding
st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="brand-mark" aria-hidden="true">
            <svg width="23" height="23" viewBox="0 0 24 24" fill="none">
                <path d="M12 3.3 5.2 5.8v5.1c0 4.5 2.8 8.5 6.8 9.8 4-1.3 6.8-5.3 6.8-9.8V5.8L12 3.3Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
                <path d="m9.5 11.8 1.8 1.8 3.5-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <div>
            <div class="brand-title">FraudGuard</div>
            <div class="brand-subtitle">ML Fraud Detection</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar navigation with custom styling
st.sidebar.markdown(
    "<div class='sidebar-section-label'>Monitoring</div>",
    unsafe_allow_html=True
)

menu_items = [
    ("Dashboard", "Dashboard"),
    ("Email Inbox", "Email Inbox"),
    ("Transactions", "Transactions"),
    ("Analytics", "Analytics"),
]

page = st.sidebar.radio(
    "Navigate",
    [item[0] for item in menu_items],
    format_func=lambda x: x,
    label_visibility="collapsed",
    key="nav_radio"
)

page = [item[1] for item in menu_items if item[0] == page][0]

# GENERATE SAMPLE TRANSACTION DATA
# ============================================================================
@st.cache_data
def generate_sample_transactions():
    """Generate simulated bank transactions with fraud indicators."""
    # Removed fixed seed to allow truly random simulations
    # np.random.seed(42)
    transactions = []
    
    # Suspicious transaction patterns
    suspicious_amounts = [850, 2500, 5000, 12000, 3200, 6700]
    suspicious_times = [2, 3, 4, 23, 22, 21]  # late-night hours
    transaction_types = ["Transfer", "Withdrawal", "Purchase", "Wire", "Card Payment", "Cash Advance"]
    locations = ["Downtown ATM", "Online Store", "International", "Local Branch", "ATM Network", "Web Transfer"]
    
    for i in range(25):
        is_suspicious = random.random() < 0.4  # 40% fraud rate in demo
        
        if is_suspicious:
            amount = random.choice(suspicious_amounts)
            hour = random.choice(suspicious_times)
            fraud_label = "HIGH"
        else:
            amount = round(random.uniform(10, 500), 2)
            hour = random.randint(6, 20)
            fraud_label = "LOW"
        
        date = datetime.now() - timedelta(days=random.randint(0, 10))
        date = date.replace(hour=hour, minute=random.randint(0, 59))
        
        fraud_score = np.random.uniform(0.85, 0.99) if is_suspicious else np.random.uniform(0.05, 0.3)
        
        transactions.append({
            "Transaction_ID": f"TXN{1000+i}",
            "Amount": amount,
            "Type": random.choice(transaction_types),
            "Time": date.strftime("%Y-%m-%d %H:%M"),
            "Location": random.choice(locations),
            "Fraud_Score": round(fraud_score, 3),
            "Risk_Level": fraud_label if fraud_score > 0.5 else ("MEDIUM" if fraud_score > 0.3 else "LOW"),
            "Timestamp": date
        })
    
    return pd.DataFrame(transactions).sort_values("Timestamp", ascending=False)


DEFAULT_FIREBASE_PROJECT_ID = (
    os.getenv("FRAUDGUARD_FIREBASE_PROJECT_ID")
    or os.getenv("GCLOUD_PROJECT")
    or os.getenv("PROJECT_ID")
    or "fraudguard-wie2003"
)
FIREBASE_API_BASE_URL = f"http://127.0.0.1:5001/{DEFAULT_FIREBASE_PROJECT_ID}/us-central1/api"
LOCAL_API_BASE_URL = "http://127.0.0.1:8787"
API_BASE_URL = os.getenv(
    "FRAUDGUARD_API_BASE_URL",
    os.getenv("FRAUDGUARD_USE_FIREBASE_EMULATOR", "").lower() in {"1", "true", "yes"}
    and FIREBASE_API_BASE_URL
    or LOCAL_API_BASE_URL,
).rstrip("/")
API_USER_ID = os.getenv("FRAUDGUARD_USER_ID", "demo-user")
ML_SERVICE_URL = os.getenv("FRAUDGUARD_ML_SERVICE_URL", "http://127.0.0.1:8000").rstrip("/")


def _api_request(api_base_url, path, *, method="GET", body=None, params=None, timeout=5.0):
    query = parse.urlencode(params or {})
    url = f"{api_base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{query}"

    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return payload.get("data", payload)


def _api_get(api_base_url, path, params=None):
    return _api_request(api_base_url, path, params=params)


def _api_post(api_base_url, path, body):
    return _api_request(api_base_url, path, method="POST", body=body)


def _predict_via_api(api_base_url, user_id, transaction):
    return _api_post(
        api_base_url,
        "/fraud/predict",
        {"userId": user_id, **transaction},
    )


def _analyze_email_via_api(api_base_url, user_id, email_content):
    return _api_post(
        api_base_url,
        "/email/analyze",
        {"userId": user_id, "emailContent": email_content},
    )


def _parse_timestamp(value):
    if not value:
        return datetime.now()

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.now()


@st.dialog("Manually Input Transaction Details")
def manual_transaction_dialog():
    st.markdown(
        """
        <style>
            div[data-testid="stDialog"] input::placeholder,
            div[data-testid="stDialog"] textarea::placeholder {
                color: #b8c0cc !important;
                opacity: 1;
            }
            div[data-testid="stDialog"] [data-baseweb="select"] span {
                color: inherit;
            }
            div[data-testid="stDialog"] [data-baseweb="select"] [aria-selected="false"] {
                color: #b8c0cc !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.text_input("User ID", value="", placeholder="user id")
    amount = st.number_input(
        "Amount (RM)",
        min_value=0.01,
        value=None,
        step=10.0,
        placeholder="0.00",
    )
    transaction_type = st.selectbox(
        "Transaction Type",
        options=["CARD_PURCHASE", "FUND_TRANSFER", "ATM_WITHDRAWAL", "ONLINE_PURCHASE"],
        index=None,
        placeholder="transaction type",
    )
    merchant = st.text_input("Merchant", value="", placeholder="merchant name")
    location = st.text_input("Location", value="", placeholder="city or region")

    date_str = st.text_input("Transaction Date", value="", placeholder="YYYY/MM/DD")
    time_str = st.text_input("Transaction Time", value="", placeholder="HH:MM")

    submit = st.button("Submit Transaction", type="primary")
    if submit:
        if not user_id.strip():
            st.error("User ID is required.")
            return
        if amount is None:
            st.error("Amount is required.")
            return
        if not transaction_type:
            st.error("Transaction type is required.")
            return
        if not merchant.strip():
            st.error("Merchant is required.")
            return
        if not location.strip():
            st.error("Location is required.")
            return
        if not date_str.strip():
            st.error("Transaction date is required.")
            return
        if not time_str.strip():
            st.error("Transaction time is required.")
            return

        parsed_date = None
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt).date()
                break
            except ValueError:
                continue
        if parsed_date is None:
            st.error("Enter a valid date (YYYY/MM/DD).")
            return

        try:
            parsed_time = datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError:
            st.error("Enter a valid time (HH:MM).")
            return

        dt_combined = datetime.combine(parsed_date, parsed_time)
        transaction_time_str = dt_combined.strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "amount": amount,
            "transactionType": transaction_type,
            "transactionTime": transaction_time_str,
            "merchant": merchant.strip(),
            "location": location.strip(),
        }
        try:
            result = _predict_via_api(API_BASE_URL, user_id.strip(), payload)
            st.session_state.latest_explanation = result.get("explanation", "")
            st.session_state.latest_suspicious_factors = result.get("suspiciousFactors", [])
            load_backend_dashboard_data.clear()
            st.session_state.pop("df_transactions", None)
            st.session_state.pop("dashboard_stats", None)
            st.rerun()
        except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
            fraud_score = 0.08
            if amount >= 5000:
                fraud_score += 0.35
            elif amount >= 1500:
                fraud_score += 0.18
            if transaction_type in {"ATM_WITHDRAWAL", "ONLINE_PURCHASE", "FUND_TRANSFER"}:
                fraud_score += 0.12
            if dt_combined.hour < 5:
                fraud_score += 0.15
            if location.strip().lower() in {"unknown", ""}:
                fraud_score += 0.1

            risk_lvl = "HIGH" if fraud_score >= 0.7 else ("MEDIUM" if fraud_score >= 0.4 else "LOW")

            factors = []
            if amount >= 5000:
                factors.append({
                    "code": "UNUSUALLY_HIGH_AMOUNT",
                    "reason": f"Transaction amount of {amount} is above the high-risk threshold.",
                    "weight": 0.35,
                    "field": "amount",
                    "observedValue": amount
                })
            elif amount >= 1500:
                factors.append({
                    "code": "ELEVATED_AMOUNT",
                    "reason": f"Transaction amount of {amount} is above the medium-risk threshold.",
                    "weight": 0.18,
                    "field": "amount",
                    "observedValue": amount
                })
            if transaction_type in {"ATM_WITHDRAWAL", "ONLINE_PURCHASE", "FUND_TRANSFER"}:
                factors.append({
                    "code": "RISKY_TRANSACTION_TYPE",
                    "reason": f"Transaction type {transaction_type} has elevated fraud exposure.",
                    "weight": 0.12,
                    "field": "transactionType",
                    "observedValue": transaction_type
                })
            if dt_combined.hour < 5:
                factors.append({
                    "code": "LATE_NIGHT_TRANSACTION",
                    "reason": "Transaction occurred between midnight and 5 AM.",
                    "weight": 0.15,
                    "field": "transactionTime",
                    "observedValue": transaction_time_str
                })
            if location.strip().lower() == "unknown":
                factors.append({
                    "code": "SUSPICIOUS_LOCATION",
                    "reason": "Location is unknown or could not be verified.",
                    "weight": 0.1,
                    "field": "location",
                    "observedValue": location.strip()
                })

            st.session_state.latest_suspicious_factors = factors
            st.session_state.latest_explanation = (
                f"{risk_lvl} risk based on {len(factors)} suspicious factor(s)."
                if factors
                else "LOW risk because no major suspicious behavior was detected."
            )

            new_row = {
                "Transaction_ID": f"TXN{random.randint(1000, 9999)}",
                "Amount": amount,
                "Type": transaction_type.replace("_", " ").title(),
                "Time": dt_combined.strftime("%Y-%m-%d %H:%M"),
                "Location": location.strip(),
                "Fraud_Score": round(min(fraud_score, 0.98), 3),
                "Risk_Level": risk_lvl,
                "Timestamp": dt_combined
            }
            st.session_state.df_transactions = pd.concat(
                [st.session_state.df_transactions, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            st.rerun()


def _analysis_to_row(item, index):
    transaction = item.get("transaction") or {}
    analysis = item.get("analysis") or item
    created_at = _parse_timestamp(item.get("createdAt") or analysis.get("analyzedAt"))
    
    # Use actual transaction time if available, otherwise fall back to analysis creation time
    txn_time_str = transaction.get("transactionTime") or transaction.get("time") or item.get("createdAt") or analysis.get("analyzedAt")
    txn_time = _parse_timestamp(txn_time_str) if txn_time_str else created_at
    
    transaction_type = transaction.get("transactionType") or transaction.get("type") or "Transaction"
    location = transaction.get("location") or transaction.get("merchant") or item.get("source") or "Unknown"

    return {
        "Transaction_ID": item.get("id") or item.get("transactionId") or f"TXN{1000 + index}",
        "Amount": float(transaction.get("amount") or item.get("amount") or 0),
        "Type": str(transaction_type).replace("_", " ").title(),
        "Time": txn_time.strftime("%Y-%m-%d %H:%M"),
        "Location": location,
        "Fraud_Score": float(analysis.get("fraudProbability") or 0),
        "Risk_Level": str(analysis.get("riskLevel") or "LOW").upper(),
        "Timestamp": txn_time,
    }


@st.cache_data(ttl=30)
def load_backend_dashboard_data(api_base_url, user_id):
    dashboard_stats = _api_get(api_base_url, "/dashboard/stats", {"userId": user_id})
    analyses_payload = _api_get(api_base_url, "/fraud/analyses", {"userId": user_id, "limit": 200})
    analyses = analyses_payload.get("analyses", analyses_payload if isinstance(analyses_payload, list) else [])
    rows = [_analysis_to_row(item, index) for index, item in enumerate(analyses)]
    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.sort_values("Timestamp", ascending=False)

    return dashboard_stats, df


# ============================================================================
# FRAUD DETECTION LOGIC
# ============================================================================
def get_risk_level_color(risk):
    """Return color code for risk level."""
    if risk == "HIGH":
        return "#ff6b6b"
    elif risk == "MEDIUM":
        return "#ffd93d"
    else:
        return "#51cf66"


def get_fraud_reasons(amount, hour, transaction_type, fraud_score=None, location=None):
    """Generate detailed, explainable fraud reasons based on transaction features."""
    reasons = []
    risk_signals = []
    normal_signals = []

    # --- Time-based analysis ---
    if hour >= 0 and hour < 5:
        risk_signals.append(
            f"Transaction occurred at {hour:02d}:{0:02d} AM — this is highly unusual, as the vast majority of "
            f"legitimate transactions happen during normal waking hours. Activity between midnight and 5 AM "
            f"is a strong indicator of unauthorized access or account compromise."
        )
    elif hour >= 21 or hour == 23:
        risk_signals.append(
            f"Transaction was initiated at {hour}:00 — late-night transactions (after 9 PM) carry elevated risk "
            f"as they fall outside typical banking hours and are commonly associated with fraudulent activity."
        )
    elif 9 <= hour <= 17:
        normal_signals.append(
            f"Transaction time ({hour:02d}:00) falls within normal business hours, which is consistent with "
            f"legitimate everyday spending."
        )

    # --- Amount-based analysis ---
    if amount > 10000:
        risk_signals.append(
            f"The transaction amount of RM{amount:,.2f} is exceptionally high — transactions above RM10,000 "
            f"are rare in typical consumer banking and often trigger regulatory review. This amount significantly "
            f"deviates from average spending patterns and warrants immediate verification."
        )
    elif amount > 5000:
        risk_signals.append(
            f"RM{amount:,.2f} is a large transaction that exceeds RM5,000 — well above the average transaction "
            f"amount. Large one-off payments are frequently exploited in scams, social engineering, and unauthorized "
            f"account usage."
        )
    elif amount > 2000:
        risk_signals.append(
            f"Transaction amount of RM{amount:,.2f} is moderately elevated. Amounts above RM2,000 represent "
            f"high-value activity that is worth reviewing, particularly when combined with other risk factors."
        )
    elif amount < 10:
        risk_signals.append(
            f"Very small transaction of RM{amount:,.2f} — fraudsters often test stolen cards with micro-transactions "
            f"before making larger purchases. This probe transaction pattern is a known fraud signal."
        )
    else:
        normal_signals.append(
            f"Amount of RM{amount:,.2f} is within a typical spending range for this transaction type."
        )

    # --- Transaction type analysis ---
    high_risk_types = ["Wire", "International Transfer", "International"]
    medium_risk_types = ["ATM Withdrawal", "Online Purchase"]
    low_risk_types = ["Bill Payment", "POS Payment"]

    if transaction_type in high_risk_types:
        risk_signals.append(
            f"'{transaction_type}' is classified as a high-risk transaction type. International and wire transfers "
            f"are irreversible once processed and are the most commonly exploited channel for financial fraud, "
            f"money mules, and romance scams. Extra verification is strongly recommended."
        )
    elif transaction_type in medium_risk_types:
        if transaction_type == "ATM Withdrawal":
            risk_signals.append(
                f"ATM withdrawals carry moderate fraud risk — physical card cloning, skimming devices, and PIN "
                f"theft are established methods used to drain accounts via ATM channels."
            )
        elif transaction_type == "Online Purchase":
            risk_signals.append(
                f"Online purchases are a common vector for card-not-present fraud, where stolen card details "
                f"are used without the physical card. This risk is heightened when combined with unusual timing "
                f"or unfamiliar merchant locations."
            )
    elif transaction_type in low_risk_types:
        normal_signals.append(
            f"'{transaction_type}' is a relatively lower-risk transaction category, typically associated with "
            f"routine, recurring payments."
        )

    # --- Location / merchant context ---
    if location:
        loc_lower = str(location).lower()
        if any(kw in loc_lower for kw in ["crypto", "bitcoin", "exchange", "forex"]):
            risk_signals.append(
                f"The merchant '{location}' appears to be a cryptocurrency or foreign exchange platform. "
                f"Transactions to crypto exchanges are frequently associated with scam fund transfers, "
                f"as they are difficult to reverse and trace."
            )
        elif any(kw in loc_lower for kw in ["unknown", "unverified", "overseas"]):
            risk_signals.append(
                f"Merchant/location '{location}' could not be verified against known merchant databases. "
                f"Unrecognised or unregistered merchants are a common characteristic of fraudulent transactions."
            )
        elif any(kw in loc_lower for kw in ["singapore", "hong kong", "international"]):
            risk_signals.append(
                f"Transaction location '{location}' is international. Cross-border transactions carry higher "
                f"fraud risk and may indicate account access from an unexpected geographic region."
            )

    # --- Fraud score context ---
    if fraud_score is not None:
        score_pct = fraud_score * 100
        if score_pct >= 85:
            risk_signals.append(
                f"The ML fraud model assigned a very high probability score of {score_pct:.1f}%. This reflects "
                f"that the transaction's combined feature profile — including amount, time, type, and behavioral "
                f"patterns — closely matches historical fraud cases in the training data."
            )
        elif score_pct >= 60:
            risk_signals.append(
                f"ML fraud probability is {score_pct:.1f}%, indicating significant concern. The model detected "
                f"multiple overlapping risk factors that collectively elevate this transaction's risk profile "
                f"beyond normal thresholds."
            )

    # Combine signals into final reasons list
    reasons = risk_signals if risk_signals else []
    if normal_signals and not risk_signals:
        reasons = normal_signals
    elif normal_signals:
        # Append a positive note if there are also normal signals
        reasons.append(
            "Note: Some transaction attributes appear normal (time or amount), but the combined risk "
            "factors above still warrant caution."
        )

    if not reasons:
        reasons.append(
            "No specific high-risk indicators were detected. Transaction attributes including time, amount, "
            "and type appear consistent with normal customer behaviour."
        )

    return reasons


# ============================================================================
# LOAD DATA
# ============================================================================
if "dashboard_stats" not in st.session_state:
    st.session_state.dashboard_stats = None

if "data_source" not in st.session_state:
    st.session_state.data_source = "sample"

if "api_error" not in st.session_state:
    st.session_state.api_error = None

if "df_transactions" not in st.session_state:
    try:
        dashboard_stats, backend_transactions = load_backend_dashboard_data(API_BASE_URL, API_USER_ID)
        if backend_transactions.empty:
            st.session_state.df_transactions = generate_sample_transactions()
            st.session_state.data_source = "sample"
            st.session_state.api_error = "Backend API connected, but no saved analyses were found yet."
        else:
            st.session_state.df_transactions = backend_transactions
            st.session_state.data_source = "api"
            st.session_state.api_error = None
        st.session_state.dashboard_stats = dashboard_stats
    except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as exc:
        st.session_state.df_transactions = generate_sample_transactions()
        st.session_state.dashboard_stats = None
        st.session_state.data_source = "sample"
        st.session_state.api_error = f"Backend API unavailable, using demo data. {exc}"

df_transactions = st.session_state.df_transactions
dashboard_stats = st.session_state.dashboard_stats or {}

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================
if page == "Dashboard":
    st.markdown(
        """
        <div class='top-strip'>
            <div class='top-strip-left'>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="4" y="3.5" width="16" height="17" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 4v16" stroke="currentColor" stroke-width="2"/>
                </svg>
                <strong>FraudGuard</strong><span>/ Real-time monitoring</span>
            </div>
            <div class='top-strip-right'><span class='status-dot'></span>Engine online</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    title_col, btn_col = st.columns(
        [10.9, 1.75],
        gap="small",
        vertical_alignment="center",
    )
    with title_col:
        st.markdown("<div class='hero-title'>Fraud Monitoring Dashboard</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='hero-sub'>Live risk analysis of incoming bank email notifications.</div>",
            unsafe_allow_html=True
        )
    with btn_col:
        if st.button("+ transaction", type="primary", use_container_width=True):
            sample = generate_sample_transactions().sample(1).iloc[0]
            try:
                result = _analyze_email_via_api(
                    API_BASE_URL,
                    API_USER_ID,
                    (
                        f"Alert: RM{sample['Amount']:,.2f} {sample['Type']} at {sample['Location']} "
                        f"on {sample['Time']}. Location: {sample['Location']}."
                    ),
                )
                # Store model reasoning for UI display
                st.session_state.latest_explanation = result.get("explanation", "")
                st.session_state.latest_suspicious_factors = result.get("suspiciousFactors", [])
                load_backend_dashboard_data.clear()
                st.session_state.pop("df_transactions", None)
                st.session_state.pop("dashboard_stats", None)
                st.session_state.api_error = None
            except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
                st.session_state.df_transactions = pd.concat(
                    [st.session_state.df_transactions, pd.DataFrame([sample])],
                    ignore_index=True,
                )
            st.rerun()

    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
    if st.session_state.data_source == "api":
        st.caption(f"Live ML-backed data from {API_BASE_URL} for user `{API_USER_ID}`.")
    elif st.session_state.api_error:
        st.warning(st.session_state.api_error)
    
    # KPI metrics aligned to reference design.
    col1, col2, col3, col4 = st.columns(4, gap="small")
    
    use_api_stats = st.session_state.data_source == "api"
    
    # Safely compute fallback and extract metrics to avoid type-checker errors on None values
    local_high_risk = len(df_transactions[df_transactions["Risk_Level"] == "HIGH"])
    local_total = len(df_transactions)
    
    local_avg_mean = df_transactions["Fraud_Score"].mean()
    local_avg_score = float(local_avg_mean) if isinstance(local_avg_mean, (int, float, np.number)) and local_avg_mean == local_avg_mean else 0.0
    
    local_blocked_sum = df_transactions[df_transactions["Risk_Level"] == "HIGH"]["Amount"].sum()
    local_blocked_exp = int(local_blocked_sum) if isinstance(local_blocked_sum, (int, float, np.number)) and local_blocked_sum == local_blocked_sum else 0

    if use_api_stats:
        hr_val = dashboard_stats.get("highRiskCount")
        high_risk_count = int(hr_val) if hr_val is not None else local_high_risk
        
        tot_val = dashboard_stats.get("totalTransactions")
        total_transactions = int(tot_val) if tot_val is not None else local_total
        
        avg_val = dashboard_stats.get("averageFraudProbability")
        avg_fraud_score = float(avg_val) if avg_val is not None else local_avg_score
        
        block_val = dashboard_stats.get("blockedExposure")
        blocked_exposure = int(block_val) if block_val is not None else local_blocked_exp
    else:
        high_risk_count = local_high_risk
        total_transactions = local_total
        avg_fraud_score = local_avg_score
        blocked_exposure = local_blocked_exp
    
    with col1:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>
                    <svg viewBox='0 0 24 24' fill='none'><path d='M4 7h16v11H4V7Z' stroke='currentColor' stroke-width='2' stroke-linejoin='round'/><path d='m4 8 8 6 8-6' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>
                </div>
                <div class='kpi-title'>TOTAL TRANSACTIONS</div>
                <div class='kpi-value'>{total_transactions}</div>
                <div class='kpi-sub'>last 7 days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-icon' style='color:#e5333f'>
                    <svg viewBox='0 0 24 24' fill='none'><path d='M12 3.5 5.5 6v5.2c0 4.2 2.6 7.7 6.5 9.3 3.9-1.6 6.5-5.1 6.5-9.3V6L12 3.5Z' stroke='currentColor' stroke-width='2' stroke-linejoin='round'/><path d='M12 8v5' stroke='currentColor' stroke-width='2' stroke-linecap='round'/><path d='M12 16.3v.2' stroke='currentColor' stroke-width='3' stroke-linecap='round'/></svg>
                </div>
                <div class='kpi-title'>HIGH RISK</div>
                <div class='kpi-value' style='color:#e5333f'>{high_risk_count}</div>
                <div class='kpi-sub'>{(high_risk_count / max(total_transactions, 1) * 100):.1f}% of total</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-icon' style='color:#e39a00'>
                    <svg viewBox='0 0 24 24' fill='none'><path d='m4 16 5-5 4 4 7-8' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/><path d='M15 7h5v5' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>
                </div>
                <div class='kpi-title'>AVG. FRAUD PROBABILITY</div>
                <div class='kpi-value' style='color:#e39a00'>{avg_fraud_score:.1%}</div>
                <div class='kpi-sub'>across all transactions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>
                    <svg viewBox='0 0 24 24' fill='none'><path d='M12 3.5 5.5 6v5.2c0 4.2 2.6 7.7 6.5 9.3 3.9-1.6 6.5-5.1 6.5-9.3V6L12 3.5Z' stroke='currentColor' stroke-width='2' stroke-linejoin='round'/><path d='m9.5 12 1.7 1.7 3.5-4' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>
                </div>
                <div class='kpi-title'>BLOCKED EXPOSURE</div>
                <div class='kpi-value'>RM{blocked_exposure:,.0f}</div>
                <div class='kpi-sub'>from high-risk events</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns([2.05, 1], gap="small")

    hourly = df_transactions.copy()
    hourly["Hour"] = hourly["Timestamp"].dt.hour
    hourly_counts = hourly.groupby(["Hour", "Risk_Level"]).size().unstack(fill_value=0)
    all_hours = pd.Index(range(24), name="Hour")
    hourly_counts = hourly_counts.reindex(all_hours, fill_value=0)
    for level in ["HIGH", "LOW"]:
        if level not in hourly_counts.columns:
            hourly_counts[level] = 0

    with chart_col1:
        with st.container(border=True):
            st.markdown("<div class='chart-title'>Hourly fraud distribution</div>", unsafe_allow_html=True)
            fig_hour = go.Figure()
            fig_hour.add_trace(
                go.Bar(
                    x=[f"{h:02d}h" for h in hourly_counts.index],
                    y=hourly_counts["LOW"],
                    marker_color="#36a269",
                    name="Low",
                    width=0.75,
                )
            )
            fig_hour.add_trace(
                go.Bar(
                    x=[f"{h:02d}h" for h in hourly_counts.index],
                    y=hourly_counts["HIGH"],
                    marker_color="#ea2239",
                    name="High",
                    width=0.75,
                )
            )
            fig_hour.update_layout(
                barmode="stack",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                margin=dict(l=38, r=8, t=10, b=26),
                height=330,
                showlegend=False,
                bargap=0.22,
            )
            fig_hour.update_xaxes(
                showgrid=True,
                gridcolor="#dbe5ef",
                tickfont=dict(size=12, color="#5d6d82"),
                zeroline=False,
            )
            fig_hour.update_yaxes(
                showgrid=True,
                gridcolor="#dbe5ef",
                tickfont=dict(size=12, color="#5d6d82"),
                rangemode="tozero",
                zeroline=False,
            )
            st.plotly_chart(fig_hour, use_container_width=True, config={"displayModeBar": False})

    with chart_col2:
        risk_counts = df_transactions["Risk_Level"].value_counts().reindex(["LOW", "MEDIUM", "HIGH"], fill_value=0)
        with st.container(border=True):
            st.markdown("<div class='chart-title'>Risk distribution</div>", unsafe_allow_html=True)
            fig_risk = go.Figure(
                data=[
                    go.Pie(
                        labels=["Low", "Medium", "High"],
                        values=risk_counts.values,
                        hole=0.55,
                        marker=dict(colors=["#35a165", "#e09a00", "#eb2039"]),
                        textinfo="none",
                        sort=False,
                    )
                ]
            )
            fig_risk.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                margin=dict(l=8, r=8, t=4, b=34),
                height=330,
                legend=dict(
                    orientation="h",
                    y=-0.04,
                    x=0.5,
                    xanchor="center",
                    font=dict(size=13),
                ),
            )
            st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    
    # Recent high-risk alerts section
    alert_title_col, alert_view_col = st.columns(
        [10, 1.2],
        gap="small",
        vertical_alignment="center",
    )
    with alert_title_col:
        st.markdown(
            "<div style='font-size: 1.8rem; font-weight: 700; color: #0f2a47; margin: 0;'>Recent high-risk alerts</div>",
            unsafe_allow_html=True
        )
    with alert_view_col:
        st.markdown(
            """
            <div style='text-align: right; margin: 0; padding: 0;'>
                <a href='/?page=Transactions' target='_self' style='text-decoration: none; color: #5f7a93; font-weight: 600; font-size: 1rem; white-space: nowrap;'>View all →</a>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    
    # Display high-risk alerts
    high_risk_alerts = df_transactions[df_transactions["Risk_Level"] == "HIGH"].head(4)
    
    for idx, row in high_risk_alerts.iterrows():
        fraud_pct = int(row["Fraud_Score"] * 100)
        hour = int(row["Time"].split()[1].split(":")[0])
        reasons = get_fraud_reasons(
            row["Amount"], hour, row["Type"],
            fraud_score=row["Fraud_Score"],
            location=row["Location"]
        )
        # Show up to 2 reasons in summary; truncate long ones for dashboard cards
        def _short(s, n=120):
            return s[:n] + "…" if len(s) > n else s
        reason_preview = " · ".join(_short(r) for r in reasons[:2])
        amount_str = "RM{:,.2f}".format(row["Amount"])
        st.markdown(
            f"""
            <div style='background: #fff5f5; border: 1px solid #f5d7d5; border-radius: 12px; padding: 1.1rem; margin-bottom: 0.8rem;'>
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem;'>
                    <div style='display: flex; align-items: center; gap: 0.8rem;'>
                        <span style='background: #e5333f; color: white; padding: 0.35rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.85rem;'>HIGH &middot; {fraud_pct}%</span>
                        <span style='color: #0f2a47; font-weight: 700; font-size: 1.05rem;'>{amount_str}</span>
                        <span style='color: #6b7b92; font-size: 0.95rem;'>&middot; {row["Type"]}</span>
                    </div>
                    <span style='color: #6b7b92; font-size: 0.92rem; font-weight: 500;'>{row["Time"]}</span>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                    <div>
                        <div style='color: #0f2a47; font-weight: 600; font-size: 0.98rem; margin-bottom: 0.3rem;'>{row["Location"]}</div>
                        <div style='color: #5f6f84; font-size: 0.9rem; line-height: 1.5;'>
                            {reason_preview}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================================
# PAGE: EMAIL INBOX
# ============================================================================
elif page == "Email Inbox":
    st.markdown(
        """
        <div class='top-strip'>
            <div class='top-strip-left'>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="4" y="3.5" width="16" height="17" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 4v16" stroke="currentColor" stroke-width="2"/>
                </svg>
                <strong>FraudGuard</strong><span>/ Real-time monitoring</span>
            </div>
            <div class='top-strip-right'><span class='status-dot'></span>Engine online</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_idx = st.session_state.get("selected_email_idx", 0)
    if selected_idx >= len(df_transactions) or selected_idx < 0:
        selected_idx = 0
    selected = df_transactions.iloc[selected_idx]
    selected_hour = int(selected["Time"].split()[1].split(":")[0])
    selected_reasons = get_fraud_reasons(selected["Amount"], selected_hour, selected["Type"])
    selected_risk = selected["Risk_Level"].lower()
    selected_probability = selected["Fraud_Score"] * 100
    selected_date = selected["Timestamp"].strftime("%d/%m/%Y, %I:%M %p").lower().replace(" 0", " ")
    selected_subject = f"Transaction Alert - RM{selected['Amount']:,.2f} {selected['Type']}"
    selected_message = (
        f"Dear customer, we detected a {selected['Type'].lower()} of RM{selected['Amount']:,.2f} "
        f"at {selected['Location']} on {selected['Timestamp'].strftime('%a %b %d %Y at %I:%M %p').lower().replace(' 0', ' ')}. "
        "If this was not you, please contact us immediately."
    )

    # Build detailed reasons using the enriched function
    selected_reasons = get_fraud_reasons(
        selected["Amount"],
        selected_hour,
        selected["Type"],
        fraud_score=selected["Fraud_Score"],
        location=selected["Location"]
    )

    # Model-derived explanation and suspicious factors, if available
    model_explanation = st.session_state.get("latest_explanation", "")
    model_factors = st.session_state.get("latest_suspicious_factors", [])

    # Build HTML for model explanation
    explanation_html = (f"<p style='margin-bottom:0.6rem;color:#374151;'>{model_explanation}</p>"
                        if model_explanation else "")

    # Build HTML list for model factors
    factors_html = ""
    if model_factors:
        factor_items = []
        for factor in model_factors:
            code = factor.get('code', '')
            reason_text = factor.get('reason', '')
            weight = factor.get('weight', 0)
            weight_str = "{:.2f}".format(weight)
            factor_items.append(
                f"<li><strong>{code}</strong>: {reason_text} "
                f"<span style='color:#9ca3af;font-size:0.85em;'>(ML weight: {weight_str})</span></li>"
            )
        factors_html = (
            "<p style='font-weight:600;margin:0.5rem 0 0.3rem;'>ML Model Signals:</p>"
            "<ul style='margin:0 0 0.5rem;'>" + "".join(factor_items) + "</ul>"
        )

    # Build rule-based / feature-derived reasons
    rule_items = "".join(
        f"<li style='margin-bottom:0.4rem;line-height:1.5;'>{r}</li>"
        for r in selected_reasons
    )
    rules_html = (
        "<p style='font-weight:600;margin:0.5rem 0 0.3rem;'>Fraud Indicators:</p>"
        f"<ul style='margin:0;padding-left:1.2rem;'>" + rule_items + "</ul>"
    )

    # Combine all reasoning sections
    combined_reason_html = explanation_html + factors_html + rules_html

    # Render the head section using columns or custom layout
    head_col, btn_col = st.columns([7, 3], vertical_alignment="center")
    with head_col:
        st.markdown(
            """
            <div class='page-head-title' style='padding: 2.2rem 0 1.65rem;'>
                <div class='page-title'>Bank Email Inbox</div>
                <div class='page-subtitle'>Simulated bank notifications, parsed and scored by the fraud engine.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with btn_col:
        # Streamlit button for "+ New email"
        # The CSS globally applies to .stButton > button giving it a beautiful styled look
        if st.button("+ New email", key="new_email_btn", use_container_width=True):
            manual_transaction_dialog()

    # Split layout into two columns using st.columns
    inbox_col1, inbox_col2 = st.columns([1, 2], gap="small")

    with inbox_col1:
        # Hidden text input to hold selection state without taking up space
        selected_idx_str = st.text_input(
            "selected_email_idx_hidden",
            value=str(selected_idx),
            key="hidden_email_idx",
            label_visibility="collapsed"
        )
        try:
            st.session_state.selected_email_idx = int(selected_idx_str)
        except ValueError:
            st.session_state.selected_email_idx = 0

        for idx, (df_index, row) in enumerate(df_transactions.head(6).iterrows()):
            risk_key = row["Risk_Level"].lower()
            subject = f"Transaction Alert - RM{row['Amount']:,.2f} {row['Type']}"
            preview = f"Dear customer, we detected a {row['Type'].lower()} of RM{row['Amount']:,.2f} ..."
            item_date = row["Timestamp"].strftime("%d/%m/%Y, %I:%M %p").lower().replace(" 0", " ")
            active_class = " mail-item-active" if idx == selected_idx else ""
            
            onclick_js = f"""
            const doc = (window.parent && window.parent.document) ? window.parent.document : document;
            const labels = doc.querySelectorAll('label');
            let input = null;
            for (let i = 0; i < labels.length; i++) {{
                if (labels[i].textContent.trim() === "selected_email_idx_hidden") {{
                    const forId = labels[i].getAttribute("for");
                    if (forId) {{
                        input = doc.getElementById(forId);
                    }}
                    break;
                }}
            }}
            if (input) {{
                input.value = "{idx}";
                input.dispatchEvent(new Event("input", {{ bubbles: true }}));
                input.dispatchEvent(new Event("change", {{ bubbles: true }}));
            }}
            """.strip().replace('\n', ' ')
            
            st.markdown(
                textwrap.dedent(f"""
                <div class='mail-item{active_class}' onclick='{onclick_js}'>
                    <div class='mail-row'>
                        <div class='mail-sender'>alerts@maybank2u.com.my</div>
                        <div class='risk-pill risk-{risk_key}'>{row['Risk_Level']}</div>
                    </div>
                    <div class='mail-subject'>{subject}</div>
                    <div class='mail-preview'>{preview}</div>
                    <div class='mail-time'>{item_date}</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )

    with inbox_col2:
        # Render the right-side cards
        detail_html = f"""
        <div class='email-card'>
            <div class='email-head'>
                <div class='email-icon'>
                    <svg width='27' height='27' viewBox='0 0 24 24' fill='none'>
                        <path d='M4 6h16v12H4V6Z' stroke='currentColor' stroke-width='2' stroke-linejoin='round'/>
                        <path d='m4 7 8 6 8-6' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/>
                    </svg>
                </div>
                <div>
                    <div class='email-subject'>{selected_subject}</div>
                    <div class='email-meta'>From alerts@maybank2u.com.my - {selected_date}</div>
                </div>
            </div>
            <div class='email-body'>{selected_message}</div>
        </div>

        <div class='analysis-card'>
            <div class='analysis-top'>
                <div class='analysis-title'>Fraud Analysis</div>
                <div class='risk-solid risk-solid-{selected_risk}'>{selected['Risk_Level']} RISK</div>
            </div>
            <div class='prob-row'>
                <div class='prob-label'>Fraud Probability</div>
                <div class='prob-value'>{selected_probability:.1f}%</div>
            </div>
            <div class='prob-track'><div class='prob-fill' style='width:{selected_probability:.1f}%'></div></div>
            <div class='detail-grid'>
                <div class='detail-box'><div class='detail-label'>Amount</div><div class='detail-value'>RM{selected['Amount']:,.2f}</div></div>
                <div class='detail-box'><div class='detail-label'>Type</div><div class='detail-value'>{selected['Type']}</div></div>
                <div class='detail-box'><div class='detail-label'>Txn ID</div><div class='detail-value'>{selected['Transaction_ID']}</div></div>
                <div class='detail-box'><div class='detail-label'>Merchant</div><div class='detail-value'>{selected['Location']}</div></div>
            </div>
            <div class='reason-label'>Why this score?</div>
            <div class='reason-list'>{combined_reason_html}</div>
        </div>
        """.strip()

        detail_html = "\n".join(line.lstrip() for line in detail_html.splitlines())
        st.markdown(detail_html, unsafe_allow_html=True)

# ============================================================================
# PAGE: TRANSACTIONS
# ============================================================================
elif page == "Transactions":
    st.markdown(
        """
        <div class='top-strip'>
            <div class='top-strip-left'>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="4" y="3.5" width="16" height="17" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 4v16" stroke="currentColor" stroke-width="2"/>
                </svg>
                <strong>FraudGuard</strong><span>/ Real-time monitoring</span>
            </div>
            <div class='top-strip-right'><span class='status-dot'></span>Engine online</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_transactions = len(df_transactions)
    table_rows = []
    for _, row in df_transactions.iterrows():
        risk_key = row["Risk_Level"].lower()
        risk_color = "#e7283b" if risk_key == "high" else ("#e39a00" if risk_key == "medium" else "#35a165")
        probability = int(round(row["Fraud_Score"] * 100))
        tx_time = row["Timestamp"].strftime("%d/%m/%Y, %I:%M %p").lower().replace(" 0", " ")
        table_rows.append(
            f"""
<tr>
<td class='tx-time'>{tx_time}</td>
<td class='tx-merchant'>{row['Location']}</td>
<td class='tx-muted'>{row['Type']}</td>
<td class='tx-muted'>{row['Location']}</td>
<td class='tx-amount'>RM{row['Amount']:,.2f}</td>
<td>
    <div class='tx-prob'>
        <div class='tx-prob-track'><div class='tx-prob-fill' style='width:{probability}%; background:{risk_color}'></div></div>
        <div class='tx-prob-text' style='color:{risk_color}'>{probability}%</div>
    </div>
</td>
<td><div class='risk-pill risk-{risk_key}'>{row['Risk_Level']}</div></td>
</tr>
""".strip()
        )

    tx_html = f"""
<div class='page-head'>
    <div>
        <div class='page-title'>Transactions</div>
        <div class='page-subtitle'>{total_transactions} of {total_transactions} transactions analyzed</div>
    </div>
</div>
<div class='tx-controls'>
    <div class='tx-search'>
        <svg width='20' height='20' viewBox='0 0 24 24' fill='none'>
            <circle cx='11' cy='11' r='7' stroke='currentColor' stroke-width='2'/>
            <path d='m16.5 16.5 3.5 3.5' stroke='currentColor' stroke-width='2' stroke-linecap='round'/>
        </svg>
        <span>Search merchant, location, type...</span>
    </div>
    <div class='tx-filter tx-filter-active'>ALL</div>
    <div class='tx-filter'>HIGH</div>
    <div class='tx-filter'>MEDIUM</div>
    <div class='tx-filter'>LOW</div>
</div>
<div class='tx-table-card'>
    <table class='tx-table'>
        <colgroup>
            <col style='width:18%'>
            <col style='width:16%'>
            <col style='width:17%'>
            <col style='width:16%'>
            <col style='width:12%'>
            <col style='width:10%'>
            <col style='width:11%'>
        </colgroup>
        <thead>
            <tr>
                <th>Time</th>
                <th>Merchant</th>
                <th>Type</th>
                <th>Location</th>
                <th style='text-align:right'>Amount</th>
                <th>Probability</th>
                <th>Risk</th>
            </tr>
        </thead>
        <tbody>{''.join(table_rows)}</tbody>
    </table>
</div>
""".strip()

    tx_html = "\n".join(line.lstrip() for line in tx_html.splitlines())
    st.markdown(tx_html, unsafe_allow_html=True)

# ============================================================================
# PAGE: ANALYTICS
# ============================================================================
elif page == "Analytics":
    st.markdown(
        """
        <div class='top-strip'>
            <div class='top-strip-left'>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="4" y="3.5" width="16" height="17" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 4v16" stroke="currentColor" stroke-width="2"/>
                </svg>
                <strong>FraudGuard</strong><span>/ Real-time monitoring</span>
            </div>
            <div class='top-strip-right'><span class='status-dot'></span>Engine online</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='page-head'>
            <div>
                <div class='page-title'>Fraud Analytics</div>
                <div class='page-subtitle'>Trends, category risk, and behavioural patterns.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_col1, chart_col2 = st.columns(2, gap="small")

    trend_df = df_transactions.copy()
    trend_df["Day"] = trend_df["Timestamp"].dt.normalize()
    end_day = trend_df["Day"].max()
    days = pd.date_range(end=end_day, periods=7, freq="D")
    day_labels = [day.strftime("%a") for day in days]
    daily_total = trend_df.groupby("Day").size().reindex(days, fill_value=0)
    daily_high = (
        trend_df[trend_df["Risk_Level"] == "HIGH"]
        .groupby("Day")
        .size()
        .reindex(days, fill_value=0)
    )

    with chart_col1:
        with st.container(border=True):
            st.markdown("<div class='chart-title'>7-day fraud trend</div>", unsafe_allow_html=True)
            fig_trend = go.Figure()
            fig_trend.add_trace(
                go.Scatter(
                    x=day_labels,
                    y=daily_total.values,
                    mode="lines+markers",
                    line=dict(color="#61738b", width=2.4, shape="spline"),
                    marker=dict(size=8, color="#ffffff", line=dict(color="#61738b", width=2)),
                    name="Analyzed",
                )
            )
            fig_trend.add_trace(
                go.Scatter(
                    x=day_labels,
                    y=daily_high.values,
                    mode="lines+markers",
                    line=dict(color="#ed1b2f", width=2.4, shape="spline"),
                    marker=dict(size=8, color="#ffffff", line=dict(color="#ed1b2f", width=2)),
                    name="High risk",
                )
            )
            fig_trend.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=330,
                margin=dict(l=44, r=10, t=10, b=28),
                showlegend=False,
            )
            fig_trend.update_xaxes(
                showgrid=True,
                gridcolor="#dbe5ef",
                tickfont=dict(size=12, color="#5d6d82"),
                zeroline=False,
            )
            fig_trend.update_yaxes(
                showgrid=True,
                gridcolor="#dbe5ef",
                tickfont=dict(size=12, color="#5d6d82"),
                rangemode="tozero",
                zeroline=False,
            )
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

    type_order = [
        "Domestic Transfer",
        "ATM Withdrawal",
        "Bill Payment",
        "POS Payment",
        "Online Purchase",
        "International Transfer",
    ]
    type_risk = df_transactions.groupby("Type")["Fraud_Score"].mean()
    fallback_risk = type_risk.mean() if not type_risk.empty else 0
    type_values = (type_risk.reindex(type_order).fillna(fallback_risk) * 100).round(1)

    with chart_col2:
        with st.container(border=True):
            st.markdown("<div class='chart-title'>Avg. fraud probability by type</div>", unsafe_allow_html=True)
            fig_type = go.Figure()
            fig_type.add_trace(
                go.Bar(
                    x=type_values.values,
                    y=type_values.index,
                    orientation="h",
                    marker_color="#d64232",
                    width=0.78,
                )
            )
            fig_type.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=330,
                margin=dict(l=176, r=10, t=10, b=28),
                showlegend=False,
            )
            fig_type.update_xaxes(
                range=[0, 60],
                tickvals=[0, 15, 30, 45, 60],
                ticktext=["0%", "15%", "30%", "45%", "60%"],
                showgrid=True,
                gridcolor="#dbe5ef",
                tickfont=dict(size=12, color="#5d6d82"),
                zeroline=False,
            )
            fig_type.update_yaxes(
                autorange="reversed",
                showgrid=True,
                gridcolor="#dbe5ef",
                tickfont=dict(size=12, color="#5d6d82"),
            )
            st.plotly_chart(fig_type, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    bottom_col1, bottom_col2 = st.columns(2, gap="small")

    location_series = df_transactions["Location"].astype(str)
    type_series = df_transactions["Type"].astype(str)
    international_mask = (
        location_series.str.contains("international|singapore|hong kong", case=False, regex=True)
        | type_series.str.contains("wire|international", case=False, regex=True)
    )
    local_avg = df_transactions.loc[~international_mask, "Fraud_Score"].mean()
    intl_avg = df_transactions.loc[international_mask, "Fraud_Score"].mean()
    overall_avg = df_transactions["Fraud_Score"].mean()
    local_pct = 0 if pd.isna(local_avg) else local_avg * 100
    intl_pct = (overall_avg if pd.isna(intl_avg) else intl_avg) * 100

    with bottom_col1:
        with st.container(border=True):
            st.markdown("<div class='chart-title'>Local vs. International risk</div>", unsafe_allow_html=True)
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge",
                    value=intl_pct,
                    domain={"x": [0.08, 0.92], "y": [0.08, 1]},
                    gauge={
                        "shape": "angular",
                        "axis": {"range": [0, 100], "visible": False},
                        "bar": {"color": "#e7283b", "thickness": 0.32},
                        "bgcolor": "#e9eaec",
                        "borderwidth": 0,
                        "steps": [
                            {"range": [0, local_pct], "color": "#35a165"},
                            {"range": [local_pct, 100], "color": "#e7283b"},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=310,
                margin=dict(l=24, r=24, t=0, b=0),
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f"""
                <div class='analytics-legend'>
                    <span><span class='legend-dot' style='background:#35a165'></span>Local: {local_pct:.1f}%</span>
                    <span><span class='legend-dot' style='background:#e7283b'></span>International: {intl_pct:.1f}%</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    summary_map = {
        "Domestic Transfer": ["Transfer", "Domestic Transfer"],
        "ATM Withdrawal": ["Withdrawal", "ATM Withdrawal"],
        "Bill Payment": ["Card Payment", "Bill Payment"],
        "POS Payment": ["Purchase", "POS Payment"],
        "Online Purchase": ["Purchase", "Online Purchase"],
        "International Transfer": ["Wire", "International Transfer"],
    }
    summary_rows = []
    for label, source_types in summary_map.items():
        type_mask = df_transactions["Type"].isin(source_types)
        total = int(type_mask.sum())
        flagged = int((type_mask & (df_transactions["Risk_Level"] == "HIGH")).sum())
        avg_pct = (
            df_transactions.loc[type_mask, "Fraud_Score"].mean() * 100
            if total
            else overall_avg * 100
        )
        fill_pct = max(0, min(100, avg_pct))
        summary_rows.append(
            f"""
            <div class='summary-row'>
                <div class='summary-line'>
                    <div class='summary-name'>{label}</div>
                    <div class='summary-meta'>{flagged} / {total} flagged · {avg_pct:.1f}%</div>
                </div>
                <div class='summary-track'><div class='summary-fill' style='width:{fill_pct:.1f}%'></div></div>
            </div>
            """
        )

    with bottom_col2:
        with st.container(border=True):
            st.markdown("<div class='chart-title'>Detection summary</div>", unsafe_allow_html=True)
            summary_html = "\n".join(line.lstrip() for line in "".join(summary_rows).splitlines())
            st.markdown(summary_html, unsafe_allow_html=True)

elif False and page == "Analytics":
    st.markdown("---")
    st.subheader("📊 Fraud Detection Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Fraud score distribution
        fig_score_dist = px.histogram(
            df_transactions,
            x="Fraud_Score",
            nbins=20,
            title="Fraud Score Distribution",
            labels={"Fraud_Score": "Fraud Probability Score"}
        )
        fig_score_dist.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Threshold")
        st.plotly_chart(fig_score_dist, use_container_width=True)
    
    with col2:
        # Transaction type risk heatmap
        type_risk = df_transactions.groupby("Type")["Fraud_Score"].mean().sort_values(ascending=False)
        fig_type = px.bar(
            x=type_risk.values,
            y=type_risk.index,
            orientation="h",
            title="Average Fraud Score by Transaction Type",
            labels={"x": "Avg Fraud Score", "y": "Transaction Type"}
        )
        st.plotly_chart(fig_type, use_container_width=True)
    
    # Fraud score trends over time
    st.markdown("---")
    df_sorted = df_transactions.sort_values("Timestamp")
    fig_trend = px.scatter(
        df_sorted,
        x="Timestamp",
        y="Fraud_Score",
        color="Risk_Level",
        size="Amount",
        hover_data=["Amount", "Type"],
        title="Fraud Score Trends Over Time",
        color_discrete_map={"HIGH": "#ff6b6b", "MEDIUM": "#ffd93d", "LOW": "#51cf66"}
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Summary statistics
    st.markdown("---")
    st.subheader("📉 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "High-Risk %",
            f"{(len(df_transactions[df_transactions['Risk_Level'] == 'HIGH']) / len(df_transactions) * 100):.1f}%"
        )
    with col2:
        st.metric("Avg. Amount (High-Risk)", f"₹{df_transactions[df_transactions['Risk_Level'] == 'HIGH']['Amount'].mean():,.2f}")
    with col3:
        st.metric("Max Fraud Score", f"{df_transactions['Fraud_Score'].max():.1%}")
    with col4:
        st.metric("Total Amount Monitored", f"₹{df_transactions['Amount'].sum():,.2f}")


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 12px;'>"
    "FraudGuard v1.0 — ML-Powered Fraud Detection | Data as of today's simulation"
    "</div>",
    unsafe_allow_html=True
)
