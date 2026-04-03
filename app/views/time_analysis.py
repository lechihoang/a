"""
Time Analysis page — price trends over time.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.analytics import monthly_price_trend, yearly_stats


def render(df: pd.DataFrame):
    st.title("📈 Time Analysis")
    st.markdown("Price trends and transaction volume over time (1995–2023).")

    tab1, tab2, tab3 = st.tabs(["Monthly Trends", "Yearly Overview", "Rolling Average"])

    with tab1:
        monthly = monthly_price_trend(df)
        monthly["year_month_dt"] = pd.to_datetime(monthly["year_month"], format="%Y-%m")

        # Dual-axis: avg price + transaction count
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["year_month_dt"],
            y=monthly["avg_price"],
            name="Avg Price (£)",
            line=dict(color="#2E86AB", width=2),
            yaxis="y1",
        ))
        fig.add_trace(go.Bar(
            x=monthly["year_month_dt"],
            y=monthly["count"],
            name="Transactions",
            marker_color="rgba(150,200,255,0.4)",
            yaxis="y2",
        ))
        fig.update_layout(
            title="Monthly Average Price vs Transaction Count",
            xaxis=dict(title="Month"),
            yaxis=dict(title="Average Price (£)", side="left", showgrid=False),
            yaxis2=dict(title="Transaction Count", side="right", overlaying="y", showgrid=False),
            legend=dict(x=0, y=1.1, orientation="h"),
            hovermode="x unified",
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Year heatmap by month
        st.subheader("Monthly Price Heatmap")
        pivot = (
            df.pivot_table(
                values="price", index="year", columns="month", aggfunc="mean"
            )
        )
        pivot.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][: len(pivot.columns)]
        fig_heat = px.imshow(
            pivot,
            labels=dict(x="Month", y="Year", color="Avg Price (£)"),
            color_continuous_scale="Viridis",
            aspect="auto",
        )
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)

    with tab2:
        yearly = yearly_stats(df)
        fig = px.bar(
            yearly,
            x="year",
            y="avg_price",
            color="avg_price",
            color_continuous_scale="RdYlGn",
            text_auto=",.0f",
            title="Average Property Price by Year",
        )
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Average Price (£)",
            showlegend=False,
            height=450,
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

        # Transaction volume by year
        fig2 = px.area(
            yearly,
            x="year",
            y="total_transactions",
            title="Total Transactions by Year",
            color_discrete_sequence=["#2E86AB"],
        )
        fig2.update_layout(
            xaxis_title="Year",
            yaxis_title="Number of Transactions",
            showlegend=False,
            height=400,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        # Rolling 12-month average
        monthly = monthly_price_trend(df)
        monthly["year_month_dt"] = pd.to_datetime(monthly["year_month"], format="%Y-%m")
        monthly = monthly.sort_values("year_month_dt")
        monthly["rolling_avg"] = monthly["avg_price"].rolling(window=12, min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["year_month_dt"],
            y=monthly["avg_price"],
            name="Monthly Avg Price",
            line=dict(color="lightgray", width=1),
            opacity=0.6,
        ))
        fig.add_trace(go.Scatter(
            x=monthly["year_month_dt"],
            y=monthly["rolling_avg"],
            name="12-Month Rolling Avg",
            line=dict(color="#E74C3C", width=3),
        ))
        fig.update_layout(
            title="12-Month Rolling Average Price",
            xaxis_title="Month",
            yaxis_title="Average Price (£)",
            legend=dict(orientation="h", y=1.1),
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)
