"""
Correlation page — distributions and correlations.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def render(df: pd.DataFrame):
    st.title("🔍 Correlation & Distribution")
    st.markdown("Statistical distributions, correlations, and price pattern analysis.")

    tab1, tab2, tab3 = st.tabs(["Price Distribution", "Trends & Correlations", "Percentiles"])

    with tab1:
        # Histogram: overall price distribution
        st.subheader("Price Distribution (Histogram)")
        # Use sample for performance on large datasets
        sample = df.sample(n=min(100_000, len(df)), random_state=42)

        fig = px.histogram(
            sample,
            x="price",
            nbins=80,
            color_discrete_sequence=["#2E86AB"],
            labels={"price": "Price (£)"},
            title=f"Price Distribution (n={min(100_000, len(df)):,} sample)",
        )
        fig.update_layout(
            xaxis_tickformat=",",
            yaxis_title="Count",
            showlegend=False,
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Log-scale histogram for better visibility
        st.subheader("Price Distribution (Log Scale)")
        fig2 = px.histogram(
            sample,
            x="price",
            nbins=100,
            color_discrete_sequence=["#E74C3C"],
            labels={"price": "Price (£)"},
            title="Log-Scale Price Distribution",
        )
        fig2.update_layout(
            xaxis_type="log",
            xaxis_tickformat=",",
            yaxis_title="Count",
            showlegend=False,
            height=400,
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Price distribution by property type (violin)
        st.subheader("Price Distribution by Property Type (Violin)")
        fig3 = px.violin(
            sample,
            x="property_type_label",
            y="price",
            color="property_type_label",
            color_discrete_sequence=px.colors.qualitative.Set2,
            box=True,
            points=False,
            labels={"price": "Price (£)"},
        )
        fig3.update_layout(
            yaxis_tickformat=",",
            showlegend=False,
            height=450,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        # Price trend: scatter with regression
        st.subheader("Price Trend Over Time (Yearly Avg)")
        yearly = (
            df.groupby("year")
            .agg(avg_price=("price", "mean"), median_price=("price", "median"))
            .reset_index()
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yearly["year"], y=yearly["avg_price"],
            name="Avg Price", mode="lines+markers",
            line=dict(color="#2E86AB", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=yearly["year"], y=yearly["median_price"],
            name="Median Price", mode="lines+markers",
            line=dict(color="#E74C3C", width=2, dash="dash"),
        ))

        # Add trendline (linear regression)
        from numpy.polynomial import polynomial as P
        x = yearly["year"].values
        y = yearly["avg_price"].values
        coefs = P.polyfit(x, y, 1)
        trendline = P.polyval(x, coefs)
        fig.add_trace(go.Scatter(
            x=x, y=trendline,
            name=f"Trend (slope: £{coefs[1]:,.0f}/yr)",
            mode="lines",
            line=dict(color="gray", width=1, dash="dot"),
        ))
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Price (£)",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Old/New comparison
        st.subheader("New Build vs Existing — Price Comparison")
        old_new_df = (
            df.groupby(["year", "old_new_label"])
            .agg(avg_price=("price", "mean"), count=("price", "count"))
            .reset_index()
        )
        fig2 = px.line(
            old_new_df,
            x="year",
            y="avg_price",
            color="old_new_label",
            color_discrete_map={"New Build": "#E74C3C", "Existing": "#2E86AB"},
            labels={"old_new_label": "Property Age", "avg_price": "Avg Price (£)"},
            line_shape="spline",
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

        # Freehold vs Leasehold
        st.subheader("Freehold vs Leasehold — Price Comparison")
        dur_df = (
            df[df["duration_label"].notna()]
            .groupby(["year", "duration_label"])
            .agg(avg_price=("price", "mean"))
            .reset_index()
        )
        fig3 = px.line(
            dur_df,
            x="year",
            y="avg_price",
            color="duration_label",
            color_discrete_map={"Freehold": "#27AE60", "Leasehold": "#F39C12"},
            line_shape="spline",
        )
        fig3.update_layout(
            xaxis_title="Year",
            yaxis_title="Average Price (£)",
            legend_title="Duration",
            height=400,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.subheader("Price Percentiles by County (Top 20)")
        pct_counties = (
            df.groupby("county_upper")["price"]
            .agg(["mean", "median", "std", "min", "max",
                  lambda x: x.quantile(0.25),
                  lambda x: x.quantile(0.75)])
            .reset_index()
        )
        pct_counties.columns = ["County", "Mean", "Median", "Std", "Min", "Max", "Q25", "Q75"]
        pct_counties = pct_counties.sort_values("Mean", ascending=False).head(20)
        pct_counties["Mean"] = pct_counties["Mean"].apply(lambda x: f"£{x:,.0f}")
        pct_counties["Median"] = pct_counties["Median"].apply(lambda x: f"£{x:,.0f}")
        pct_counties["Q25"] = pct_counties["Q25"].apply(lambda x: f"£{x:,.0f}")
        pct_counties["Q75"] = pct_counties["Q75"].apply(lambda x: f"£{x:,.0f}")
        pct_counties["Min"] = pct_counties["Min"].apply(lambda x: f"£{x:,.0f}")
        pct_counties["Max"] = pct_counties["Max"].apply(lambda x: f"£{x:,.0f}")
        pct_counties["Std"] = pct_counties["Std"].apply(lambda x: f"£{x:,.0f}")
        st.dataframe(pct_counties, use_container_width=True, height=600, hide_index=True)

        # Percentile range chart
        st.subheader("Price Range by County (Min–Max with IQR)")
        pct_range = pct_counties.copy()
        pct_range = (
            df.groupby("county_upper")["price"]
            .agg(["mean", "min", "max",
                  lambda x: x.quantile(0.25),
                  lambda x: x.quantile(0.75)])
            .reset_index()
        )
        pct_range.columns = ["County", "mean", "min", "max", "q25", "q75"]
        pct_range = pct_range.sort_values("mean", ascending=False).head(15)
        fig4 = go.Figure()
        for _, row in pct_range.iterrows():
            fig4.add_trace(go.Bar(
                x=[row["County"]],
                y=[row["mean"]],
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[row["max"] - row["mean"]],
                    arrayminus=[row["mean"] - row["min"]],
                ),
                marker_color="#2E86AB",
                name=row["County"],
            ))
        fig4.update_layout(
            xaxis_title="County",
            yaxis_title="Average Price (£)",
            yaxis_tickformat=",",
            showlegend=False,
            height=500,
        )
        st.plotly_chart(fig4, use_container_width=True)
