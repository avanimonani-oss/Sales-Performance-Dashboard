"""Interactive sales dashboard — run: streamlit run dashboard/app.py"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data" / "sales_data.csv"

st.set_page_config(page_title="Sales Performance", layout="wide", page_icon="📊")


@st.cache_data
def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["Order_Date"])
    df["Year"] = df["Order_Date"].dt.year
    df["YearMonth"] = df["Order_Date"].dt.to_period("M").astype(str)
    return df


df = load()

st.title("Sales Performance Dashboard")
st.caption("2021–2024 · 50,000 orders · Live from sales_data.csv")

page = st.sidebar.radio("Page", ["Executive Overview", "Product Analysis", "Customer Analysis"])

if page == "Executive Overview":
    regions = st.sidebar.multiselect(
        "Region", sorted(df["Region"].unique()), default=sorted(df["Region"].unique())
    )
    categories = st.sidebar.multiselect(
        "Category", sorted(df["Category"].unique()), default=sorted(df["Category"].unique())
    )
    years = st.sidebar.multiselect(
        "Year", sorted(df["Year"].unique()), default=sorted(df["Year"].unique())
    )

    f = df[df["Region"].isin(regions) & df["Category"].isin(categories) & df["Year"].isin(years)]
    rev, profit = f["Sales"].sum(), f["Profit"].sum()
    orders = f["Order_ID"].nunique()
    aov = rev / orders if orders else 0
    margin = profit / rev * 100 if rev else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Revenue", f"${rev:,.0f}")
    k2.metric("Total Profit", f"${profit:,.0f}")
    k3.metric("Total Orders", f"{orders:,}")
    k4.metric("Avg Order Value", f"${aov:,.0f}")
    k5.metric("Profit Margin", f"{margin:.2f}%")

    left, right = st.columns([3, 1])
    monthly = f.groupby("YearMonth")["Sales"].sum().reset_index()
    left.plotly_chart(px.line(monthly, x="YearMonth", y="Sales", title="Monthly Revenue Trend"), use_container_width=True)
    seg = f.groupby("Segment")["Sales"].sum().reset_index()
    right.plotly_chart(px.pie(seg, names="Segment", values="Sales", title="Revenue by Segment", hole=0.45), use_container_width=True)

    b1, b2 = st.columns(2)
    reg = f.groupby("Region")["Sales"].sum().reset_index().sort_values("Sales")
    b1.plotly_chart(px.bar(reg, x="Sales", y="Region", orientation="h", title="Revenue by Region"), use_container_width=True)
    cat = f.groupby("Category")["Profit"].sum().reset_index()
    b2.plotly_chart(px.bar(cat, x="Category", y="Profit", title="Profit by Category"), use_container_width=True)

elif page == "Product Analysis":
    p1, p2 = st.columns(2)
    top_rev = df.groupby("Product_Name")["Sales"].sum().nlargest(10).reset_index()
    top_profit = df.groupby("Product_Name")["Profit"].sum().nlargest(10).reset_index()
    p1.plotly_chart(px.bar(top_rev.sort_values("Sales"), x="Sales", y="Product_Name", orientation="h", title="Top 10 by Revenue"), use_container_width=True)
    p2.plotly_chart(px.bar(top_profit.sort_values("Profit"), x="Profit", y="Product_Name", orientation="h", title="Top 10 by Profit"), use_container_width=True)

    p3, p4 = st.columns(2)
    p3.plotly_chart(px.bar(df.groupby("Category")["Sales"].sum().reset_index(), x="Category", y="Sales", title="Revenue by Category"), use_container_width=True)
    sub = df.groupby("Sub_Category")["Sales"].sum().nlargest(12).reset_index()
    p4.plotly_chart(px.bar(sub.sort_values("Sales"), x="Sales", y="Sub_Category", orientation="h", title="Revenue by Subcategory"), use_container_width=True)

    qty = df.groupby("Product_Name")["Quantity"].sum().nlargest(15).reset_index()
    st.plotly_chart(px.bar(qty.sort_values("Quantity"), x="Quantity", y="Product_Name", orientation="h", title="Quantity Sold (Top 15)"), use_container_width=True)

else:
    cust = df.groupby(["Customer_Name", "Segment"]).agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique")).reset_index()
    c1, c2 = st.columns(2)
    top = cust.nlargest(10, "Revenue").sort_values("Revenue")
    c1.dataframe(top.style.format({"Revenue": "${:,.0f}", "Profit": "${:,.0f}"}), use_container_width=True, hide_index=True)
    seg = df.groupby("Segment")["Sales"].sum().reset_index()
    c2.plotly_chart(px.bar(seg, x="Segment", y="Sales", title="Revenue by Segment"), use_container_width=True)

    c3, c4 = st.columns(2)
    c3.plotly_chart(px.bar(top, x="Customer_Name", y="Revenue", title="Customer Contribution (Top 10)"), use_container_width=True)
    top_ord = cust.nlargest(10, "Orders").sort_values("Orders")
    c4.plotly_chart(px.bar(top_ord, x="Orders", y="Customer_Name", orientation="h", title="Orders by Customer"), use_container_width=True)

    def band(v):
        if v >= 5e6: return "≥ $5M"
        if v >= 2e6: return "$2M – $5M"
        if v >= 1e6: return "$1M – $2M"
        if v >= 5e5: return "$500K – $1M"
        return "< $500K"

    cust["Band"] = cust["Revenue"].apply(band)
    bands = cust["Band"].value_counts().reindex(["< $500K", "$500K – $1M", "$1M – $2M", "$2M – $5M", "≥ $5M"]).fillna(0)
    st.plotly_chart(px.bar(bands.reset_index(), x="Band", y="count", title="Revenue Distribution"), use_container_width=True)
