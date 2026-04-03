"""
Analytics helpers — aggregation and filtering utilities.
"""

import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    date_range: tuple,
    counties: list,
    property_types: list,
    old_new: str,
) -> pd.DataFrame:
    """Apply sidebar filters and return filtered DataFrame."""
    filtered = df.copy()

    # Date filter
    date_start, date_end = date_range
    if date_start and date_end:
        filtered = filtered[
            (filtered["Date_of_Transfer"] >= pd.to_datetime(date_start)) &
            (filtered["Date_of_Transfer"] <= pd.to_datetime(date_end))
        ]

    # County filter
    if counties:
        filtered = filtered[filtered["county_upper"].isin(counties)]

    # Property type filter
    if property_types:
        filtered = filtered[filtered["property_type_label"].isin(property_types)]

    # Old/New filter
    if old_new == "New Build":
        filtered = filtered[filtered["Old/New"] == "Y"]
    elif old_new == "Existing":
        filtered = filtered[filtered["Old/New"] == "N"]

    return filtered


def kpi_stats(df: pd.DataFrame) -> dict:
    """Return KPI metrics for the filtered DataFrame."""
    return {
        "total_transactions": len(df),
        "avg_price": df["price"].mean(),
        "median_price": df["price"].median(),
        "max_price": df["price"].max(),
        "min_price": df["price"].min(),
        "total_value": df["price"].sum(),
    }


def monthly_price_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly average and total transaction count."""
    return (
        df.groupby("year_month")
        .agg(avg_price=("price", "mean"), count=("price", "count"))
        .reset_index()
        .sort_values("year_month")
    )


def yearly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Yearly aggregated stats."""
    return (
        df.groupby("year")
        .agg(
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            total_transactions=("price", "count"),
            total_value=("price", "sum"),
        )
        .reset_index()
        .sort_values("year")
    )


def county_stats(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Top N counties by average price."""
    return (
        df.groupby("county_upper")
        .agg(
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            total_transactions=("price", "count"),
        )
        .reset_index()
        .sort_values("avg_price", ascending=False)
        .head(top_n)
    )


def property_type_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Stats by property type."""
    return (
        df.groupby("property_type_label")
        .agg(
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            total_transactions=("price", "count"),
        )
        .reset_index()
        .sort_values("avg_price", ascending=False)
    )


def district_stats(df: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    """Top N districts by average price."""
    return (
        df.groupby("District")
        .agg(
            avg_price=("price", "mean"),
            total_transactions=("price", "count"),
        )
        .reset_index()
        .sort_values("avg_price", ascending=False)
        .head(top_n)
    )
