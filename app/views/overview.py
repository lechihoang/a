"""
Overview page — KPI cards and summary statistics.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.analytics import kpi_stats, county_stats, property_type_stats


def render(df: pd.DataFrame, df_all: pd.DataFrame = None):
    st.title("📊 Overview")
    st.markdown("Key performance indicators and summary statistics for UK property transactions.")

    stats = kpi_stats(df)

    # ── KPI Cards ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Transactions",
        f"{stats['total_transactions']:,.0f}",
        delta=f"{stats['total_transactions']:,.0f} sales",
    )
    col2.metric(
        "Average Price",
        f"£{stats['avg_price']:,.0f}",
        delta=f"£{stats['median_price']:,.0f} median",
    )
    col3.metric(
        "Median Price",
        f"£{stats['median_price']:,.0f}",
    )
    col4.metric(
        "Max Price",
        f"£{stats['max_price']:,.0f}",
        delta=f"£{stats['min_price']:,.0f} min",
    )

    st.markdown("---")

    # ── Summary Tables ─────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Top 10 Counties by Avg Price")
        top_counties = county_stats(df, top_n=10)
        fig = px.bar(
            top_counties,
            x="county_upper",
            y="avg_price",
            color="avg_price",
            color_continuous_scale="Viridis",
            text_auto=",.0f",
        )
        fig.update_layout(
            xaxis_title="County",
            yaxis_title="Average Price (£)",
            showlegend=False,
            xaxis_tickangle=-45,
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Top 10 Counties by Transaction Volume")
        vol_counties = (
            df.groupby("county_upper")
            .agg(volume=("price", "count"))
            .reset_index()
            .sort_values("volume", ascending=False)
            .head(10)
        )
        fig2 = px.bar(
            vol_counties,
            x="county_upper",
            y="volume",
            color="volume",
            color_continuous_scale="Blues",
            text_auto=",",
        )
        fig2.update_layout(
            xaxis_title="County",
            yaxis_title="Number of Transactions",
            showlegend=False,
            xaxis_tickangle=-45,
        )
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ── Property Type Distribution ─────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Avg Price by Property Type")
        pt_stats = property_type_stats(df)
        fig3 = px.bar(
            pt_stats,
            x="property_type_label",
            y="avg_price",
            color="avg_price",
            color_continuous_scale="RdYlGn",
            text_auto=",.0f",
        )
        fig3.update_layout(
            xaxis_title="Property Type",
            yaxis_title="Average Price (£)",
            showlegend=False,
        )
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.subheader("Transactions by Property Type")
        pt_vol = (
            df.groupby("property_type_label")
            .agg(volume=("price", "count"))
            .reset_index()
            .sort_values("volume", ascending=False)
        )
        fig4 = px.pie(
            pt_vol,
            names="property_type_label",
            values="volume",
            hole=0.4,
            color="property_type_label",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig4.update_traces(text=pt_vol["volume"].apply(lambda x: f"{x:,}"))
        st.plotly_chart(fig4, use_container_width=True)

    # ── Data Table ─────────────────────────────────────────────────────────────
    with st.expander("📋 View Filtered Data Table"):
        st.dataframe(
            df[["Transaction_unique_identifier", "price", "Date_of_Transfer", "postcode",
                "property_type_label", "county_upper", "Town/City"]]
            .head(1000)
            .sort_values("Date_of_Transfer", ascending=False),
            use_container_width=True,
            height=400,
        )
