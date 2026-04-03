"""
Property Analysis page — property type breakdown.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.analytics import property_type_stats


def render(df: pd.DataFrame):
    st.title("🏠 Property Analysis")
    st.markdown("Breakdown of property types, prices, and trends across property categories.")

    col1, col2 = st.columns(2)

    # Pie chart: property type distribution
    with col1:
        st.subheader("Transaction Volume by Property Type")
        dist = (
            df.groupby("property_type_label")
            .agg(count=("price", "count"))
            .reset_index()
            .sort_values("count", ascending=False)
        )
        fig = px.pie(
            dist,
            names="property_type_label",
            values="count",
            hole=0.45,
            color="property_type_label",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(
            textinfo="percent+label",
            textposition="inside",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Bar chart: avg price by type
    with col2:
        st.subheader("Average Price by Property Type")
        pt_stats = property_type_stats(df)
        fig2 = px.bar(
            pt_stats,
            x="property_type_label",
            y="avg_price",
            color="avg_price",
            color_continuous_scale="RdYlGn",
            text_auto=",.0f",
        )
        fig2.update_layout(
            xaxis_title="Property Type",
            yaxis_title="Average Price (£)",
            showlegend=False,
        )
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Box plot: price distribution by property type
    st.subheader("Price Distribution by Property Type")
    fig3 = px.box(
        df,
        x="property_type_label",
        y="price",
        color="property_type_label",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"price": "Price (£)", "property_type_label": "Property Type"},
        points=False,
    )
    fig3.update_layout(
        yaxis_tickformat=",",
        showlegend=False,
        height=450,
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Stacked bar: property type volume over time
    st.subheader("Property Type Volume Over Time")
    yearly_type = (
        df.groupby(["year", "property_type_label"])
        .agg(count=("price", "count"))
        .reset_index()
    )
    fig4 = px.area(
        yearly_type,
        x="year",
        y="count",
        color="property_type_label",
        color_discrete_sequence=px.colors.qualitative.Set2,
        groupnorm="",
    )
    fig4.update_layout(
        xaxis_title="Year",
        yaxis_title="Number of Transactions",
        legend_title="Property Type",
        height=450,
    )
    st.plotly_chart(fig4, use_container_width=True)

    # Median price trend by property type
    st.subheader("Median Price Trend by Property Type")
    median_trend = (
        df.groupby(["year_month", "property_type_label"])
        .agg(median_price=("price", "median"))
        .reset_index()
    )
    fig5 = px.line(
        median_trend,
        x="year_month",
        y="median_price",
        color="property_type_label",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"year_month": "Month", "median_price": "Median Price (£)"},
        line_shape="spline",
    )
    fig5.update_layout(
        xaxis_title="Month",
        yaxis_title="Median Price (£)",
        legend_title="Property Type",
        height=450,
    )
    st.plotly_chart(fig5, use_container_width=True)
