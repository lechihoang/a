"""
Spatial Analysis page — geographic breakdown.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.analytics import county_stats, district_stats


def render(df: pd.DataFrame):
    st.title("🗺️ Spatial Analysis")
    st.markdown("Geographic breakdown of UK property prices by county and district.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Top 20 Counties by Avg Price")
        top_c = county_stats(df, top_n=20)
        fig = px.bar(
            top_c,
            x="avg_price",
            y="county_upper",
            orientation="h",
            color="avg_price",
            color_continuous_scale="Viridis",
            text_auto=",.0f",
            title="Average Price by County",
        )
        fig.update_layout(
            xaxis_title="Average Price (£)",
            yaxis_title="",
            showlegend=False,
            height=600,
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 20 Counties by Transaction Volume")
        vol = (
            df.groupby("county_upper")
            .agg(volume=("price", "count"))
            .reset_index()
            .sort_values("volume", ascending=False)
            .head(20)
        )
        fig2 = px.bar(
            vol,
            x="volume",
            y="county_upper",
            orientation="h",
            color="volume",
            color_continuous_scale="Blues",
            text_auto=",",
        )
        fig2.update_layout(
            xaxis_title="Number of Transactions",
            yaxis_title="",
            showlegend=False,
            height=600,
        )
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # District level
    st.subheader("Top 30 Districts by Avg Price")
    top_d = district_stats(df, top_n=30)
    fig3 = px.bar(
        top_d,
        x="avg_price",
        y="District",
        orientation="h",
        color="avg_price",
        color_continuous_scale="RdYlGn",
        text_auto=",.0f",
    )
    fig3.update_layout(
        xaxis_title="Average Price (£)",
        yaxis_title="",
        showlegend=False,
        height=700,
    )
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

    # Scatter: volume vs avg price by county
    st.subheader("County: Price vs Volume")
    scatter_df = (
        df.groupby("county_upper")
        .agg(avg_price=("price", "mean"), volume=("price", "count"))
        .reset_index()
    )
    fig4 = px.scatter(
        scatter_df,
        x="volume",
        y="avg_price",
        size="avg_price",
        color="avg_price",
        color_continuous_scale="Viridis",
        hover_name="county_upper",
        hover_data={"volume": ":,", "avg_price": "£{:,.0f}"},
        size_max=60,
    )
    fig4.update_layout(
        xaxis_title="Number of Transactions (volume)",
        yaxis_title="Average Price (£)",
        height=500,
    )
    st.plotly_chart(fig4, use_container_width=True)
