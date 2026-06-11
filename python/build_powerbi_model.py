"""Build star-schema CSV files in data/model/."""

import os
from datetime import datetime, timedelta

import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "sales_data.csv")
OUT = os.path.join(ROOT, "data", "model")


def build_dim_date(start: str, end: str) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="D")
    df = pd.DataFrame({"Date": dates})
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Date"].dt.strftime("%B")
    df["Quarter"] = df["Date"].dt.quarter
    df["QuarterLabel"] = "Q" + df["Quarter"].astype(str)
    df["YearMonth"] = df["Date"].dt.strftime("%Y-%m")
    df["Date"] = df["Date"].dt.date
    return df


def build():
    os.makedirs(OUT, exist_ok=True)
    raw = pd.read_csv(RAW, parse_dates=["Order_Date"])

    raw["GeographyKey"] = (
        raw["Region"].astype(str)
        + "|"
        + raw["State"].astype(str)
        + "|"
        + raw["City"].astype(str)
    )

    fact = raw[
        [
            "Order_ID",
            "Order_Date",
            "Customer_ID",
            "Product_Name",
            "GeographyKey",
            "Sales",
            "Quantity",
            "Discount",
            "Profit",
        ]
    ].copy()
    fact["Order_Date"] = pd.to_datetime(fact["Order_Date"]).dt.date

    dim_customer = (
        raw[["Customer_ID", "Customer_Name", "Segment"]]
        .drop_duplicates(subset=["Customer_ID"])
        .sort_values("Customer_ID")
        .reset_index(drop=True)
    )

    dim_product = (
        raw[["Product_Name", "Category", "Sub_Category"]]
        .drop_duplicates(subset=["Product_Name"])
        .sort_values("Product_Name")
        .reset_index(drop=True)
    )

    dim_geography = (
        raw[["GeographyKey", "Region", "State", "City"]]
        .drop_duplicates(subset=["GeographyKey"])
        .sort_values(["Region", "State", "City"])
        .reset_index(drop=True)
    )

    dim_date = build_dim_date("2021-01-01", "2024-12-31")

    customer_revenue = (
        fact.groupby("Customer_ID")["Sales"]
        .sum()
        .reset_index()
        .rename(columns={"Sales": "Customer_Total_Revenue"})
    )
    dim_customer = dim_customer.merge(customer_revenue, on="Customer_ID", how="left")

    def revenue_band(value: float) -> str:
        if value >= 5_000_000:
            return "≥ $5M"
        if value >= 2_000_000:
            return "$2M – $5M"
        if value >= 1_000_000:
            return "$1M – $2M"
        if value >= 500_000:
            return "$500K – $1M"
        return "< $500K"

    band_sort = {
        "< $500K": 1,
        "$500K – $1M": 2,
        "$1M – $2M": 3,
        "$2M – $5M": 4,
        "≥ $5M": 5,
    }
    dim_customer["Revenue_Band"] = dim_customer["Customer_Total_Revenue"].apply(revenue_band)
    dim_customer["Revenue_Band_Sort"] = dim_customer["Revenue_Band"].map(band_sort)

    fact.to_csv(os.path.join(OUT, "Fact_Sales.csv"), index=False)
    dim_date.to_csv(os.path.join(OUT, "Dim_Date.csv"), index=False)
    dim_customer.to_csv(os.path.join(OUT, "Dim_Customer.csv"), index=False)
    dim_product.to_csv(os.path.join(OUT, "Dim_Product.csv"), index=False)
    dim_geography.to_csv(os.path.join(OUT, "Dim_Geography.csv"), index=False)

    print(f"Wrote {len(fact):,} rows -> Fact_Sales.csv")
    print(f"Wrote {len(dim_date):,} rows -> Dim_Date.csv")
    print(f"Wrote {len(dim_customer):,} rows -> Dim_Customer.csv")
    print(f"Wrote {len(dim_product):,} rows -> Dim_Product.csv")
    print(f"Wrote {len(dim_geography):,} rows -> Dim_Geography.csv")
    print(f"Output directory: {OUT}")


if __name__ == "__main__":
    build()
