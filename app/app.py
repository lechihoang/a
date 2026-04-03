"""
UK Property Price Analytics — Streamlit Dashboard
"""

import os
from datetime import date

import streamlit as st
from dotenv import load_dotenv

# Must load env before imports
load_dotenv()

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="UK Property Analytics(Version 1)",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data Loading ───────────────────────────────────────────────────────────────

from src.data_loader import get_data
from src.analytics import apply_filters

try:
    df_all = get_data()
except FileNotFoundError:
    st.error("Data file not found. Please run ETL first.")
    st.stop()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Ensure derived columns exist
if "year_month" not in df_all.columns:
    df_all["year_month"] = df_all["Date_of_Transfer"].dt.strftime("%Y-%m")
if "year" not in df_all.columns:
    df_all["year"] = df_all["Date_of_Transfer"].dt.year
if "month" not in df_all.columns:
    df_all["month"] = df_all["Date_of_Transfer"].dt.month

# Ensure derived columns exist
if "year_month" not in df_all.columns:
    df_all["year_month"] = df_all["Date_of_Transfer"].dt.strftime("%Y-%m")
if "year" not in df_all.columns:
    df_all["year"] = df_all["Date_of_Transfer"].dt.year
if "month" not in df_all.columns:
    df_all["month"] = df_all["Date_of_Transfer"].dt.month

# ── Sidebar Filters ───────────────────────────────────────────────────────────

st.sidebar.title("🏠 UK Property Analytics")
st.sidebar.markdown("---")
st.sidebar.header("Filters")

# Date range
min_date = df_all["Date_of_Transfer"].min().date()
max_date = df_all["Date_of_Transfer"].max().date()

default_start = max(min_date, date(2020, 1, 1))
date_range = st.sidebar.date_input(
    "Date Range",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY",
)

# County multi-select (top 20 by volume)
top_counties = (
    df_all.groupby("county_upper")
    .size()
    .sort_values(ascending=False)
    .head(30)
    .index.tolist()
)
selected_counties = st.sidebar.multiselect(
    "County",
    options=top_counties,
    default=[c for c in ["LONDON", "GREATER MANCHESTER", "WEST MIDLANDS", "WEST YORKSHIRE", "KENT"] if c in top_counties],
)

# Property type
all_property_types = sorted(df_all["property_type_label"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect(
    "Property Type",
    options=all_property_types,
    default=all_property_types,
)

# Old/New
old_new_options = ["All", "New Build", "Existing"]
selected_old_new = st.sidebar.radio("Property Age", old_new_options)

st.sidebar.markdown("---")
st.sidebar.caption(f"Total records: **{len(df_all):,}**")
st.sidebar.caption(f"Date range: {min_date.strftime('%b %Y')} – {max_date.strftime('%b %Y')}")

# ── Apply Filters ───────────────────────────────────────────────────────────────

df = apply_filters(
    df_all,
    date_range,
    selected_counties if selected_counties else [],
    selected_types,
    selected_old_new,
)

if df.empty:
    st.warning("No data matches the selected filters. Try adjusting the filters.")
    st.stop()

# ── Navigation ─────────────────────────────────────────────────────────────────

PAGES = {
    "📊 Overview": "overview",
    "📈 Time Analysis": "time_analysis",
    "🗺️ Spatial Analysis": "spatial_analysis",
    "🏠 Property Analysis": "property_analysis",
    "🔍 Correlation": "correlation",
}

st.sidebar.markdown("---")
st.sidebar.subheader("Pages")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# ── Dynamic Page Loading ───────────────────────────────────────────────────────

page_name = PAGES[selection]

if page_name == "overview":
    from views import overview
    overview.render(df, df_all)
elif page_name == "time_analysis":
    from views import time_analysis
    time_analysis.render(df)
elif page_name == "spatial_analysis":
    from views import spatial_analysis
    spatial_analysis.render(df)
elif page_name == "property_analysis":
    from views import property_analysis
    property_analysis.render(df)
elif page_name == "correlation":
    from views import correlation
    correlation.render(df)
