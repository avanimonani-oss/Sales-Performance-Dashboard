"""
Generate real dashboard charts and page composites from sales_data.csv.
Run: python python/generate_dashboard_charts.py
"""

import os
from textwrap import shorten

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.table import Table

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data", "sales_data.csv")
IMAGES = os.path.join(ROOT, "images")

COLORS = {
    "bg": "#F5F7FA",
    "card": "#FFFFFF",
    "border": "#E5E7EB",
    "text": "#1F2937",
    "muted": "#6B7280",
    "accent": "#2563EB",
    "profit": "#059669",
    "palette": ["#2563EB", "#059669", "#7C3AED", "#D97706", "#DC2626", "#0891B2"],
}


def load():
    df = pd.read_csv(DATA, parse_dates=["Order_Date"])
    return df


def fmt_currency(v):
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:,.0f}"


def style_axes(ax, title):
    ax.set_title(title, fontsize=11, fontweight="600", color=COLORS["text"], loc="left", pad=8)
    ax.tick_params(colors=COLORS["muted"], labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(COLORS["border"])
    ax.set_facecolor(COLORS["card"])


def kpi_card(fig, spec, label, value, subtitle=""):
    ax = fig.add_subplot(spec)
    ax.set_facecolor(COLORS["card"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    rect = mpatches.FancyBboxPatch(
        (0.02, 0.05), 0.96, 0.9,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1, edgecolor=COLORS["border"], facecolor=COLORS["card"],
    )
    ax.add_patch(rect)
    ax.text(0.08, 0.62, value, fontsize=16, fontweight="700", color=COLORS["text"], va="center")
    ax.text(0.08, 0.32, label, fontsize=9, color=COLORS["muted"], va="center")
    if subtitle:
        ax.text(0.08, 0.14, subtitle, fontsize=8, color=COLORS["muted"], va="center")


def build_executive(df):
    total_rev = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order_ID"].nunique()
    aov = df.groupby("Order_ID")["Sales"].sum().mean()
    margin = total_profit / total_rev * 100

    monthly = (
        df.assign(YearMonth=df["Order_Date"].dt.to_period("M").astype(str))
        .groupby("YearMonth")["Sales"].sum()
        .sort_index()
    )
    by_region = df.groupby("Region")["Sales"].sum().sort_values(ascending=True)
    by_category_profit = df.groupby("Category")["Profit"].sum()
    by_segment = df.groupby("Segment")["Sales"].sum()

    fig = plt.figure(figsize=(16, 9), facecolor=COLORS["bg"])
    fig.suptitle(
        "Sales Performance Dashboard — Executive Overview",
        fontsize=16, fontweight="700", color=COLORS["text"], x=0.02, y=0.97, ha="left",
    )

    gs = gridspec.GridSpec(3, 6, figure=fig, height_ratios=[0.55, 1.2, 1], hspace=0.45, wspace=0.35)

    kpi_card(fig, gs[0, 0], "Total Revenue", fmt_currency(total_rev))
    kpi_card(fig, gs[0, 1], "Total Profit", fmt_currency(total_profit))
    kpi_card(fig, gs[0, 2], "Total Orders", f"{total_orders:,}")
    kpi_card(fig, gs[0, 3], "Average Order Value", fmt_currency(aov))
    kpi_card(fig, gs[0, 4], "Profit Margin %", f"{margin:.2f}%")

    ax_trend = fig.add_subplot(gs[1, :4])
    ax_trend.plot(range(len(monthly)), monthly.values, color=COLORS["accent"], linewidth=2)
    ax_trend.fill_between(range(len(monthly)), monthly.values, alpha=0.12, color=COLORS["accent"])
    step = max(1, len(monthly) // 8)
    ax_trend.set_xticks(range(0, len(monthly), step))
    ax_trend.set_xticklabels(monthly.index[::step], rotation=45, ha="right")
    ax_trend.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax_trend, "Monthly Revenue Trend")

    ax_donut = fig.add_subplot(gs[1, 4:])
    wedges, _, autotexts = ax_donut.pie(
        by_segment.values, labels=None, autopct="%1.0f%%",
        colors=COLORS["palette"][: len(by_segment)], startangle=90,
        wedgeprops=dict(width=0.45, edgecolor=COLORS["card"]),
        textprops=dict(color=COLORS["text"], fontsize=9),
    )
    ax_donut.legend(
        by_segment.index, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8, frameon=False,
    )
    style_axes(ax_donut, "Revenue by Segment")
    ax_donut.set_aspect("equal")

    ax_reg = fig.add_subplot(gs[2, :2])
    ax_reg.barh(by_region.index, by_region.values, color=COLORS["accent"])
    ax_reg.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax_reg, "Revenue by Region")

    ax_cat = fig.add_subplot(gs[2, 2:4])
    ax_cat.bar(by_category_profit.index, by_category_profit.values, color=COLORS["profit"])
    ax_cat.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax_cat, "Profit by Category")

    ax_meta = fig.add_subplot(gs[2, 4:])
    ax_meta.axis("off")
    meta = (
        f"Data: sales_data.csv  |  {len(df):,} rows  |  "
        f"{df['Order_Date'].min().date()} to {df['Order_Date'].max().date()}\n"
        f"Regions: {', '.join(sorted(df['Region'].unique()))}\n"
        f"Categories: {', '.join(sorted(df['Category'].unique()))}"
    )
    ax_meta.text(0.05, 0.5, meta, fontsize=9, color=COLORS["muted"], va="center")

    out = os.path.join(IMAGES, "executive_dashboard.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close(fig)
    return out


def build_product(df):
    top_rev = (
        df.groupby("Product_Name")["Sales"].sum().nlargest(10).sort_values()
    )
    top_profit = (
        df.groupby("Product_Name")["Profit"].sum().nlargest(10).sort_values()
    )
    by_cat = df.groupby("Category")["Sales"].sum()
    by_sub = df.groupby("Sub_Category")["Sales"].sum().nlargest(12).sort_values()
    top_qty = (
        df.groupby("Product_Name")["Quantity"].sum().nlargest(15).sort_values()
    )

    fig = plt.figure(figsize=(16, 10), facecolor=COLORS["bg"])
    fig.suptitle("Product Analysis", fontsize=16, fontweight="700", color=COLORS["text"], x=0.02, y=0.97, ha="left")
    gs = gridspec.GridSpec(3, 2, figure=fig, height_ratios=[1, 1, 1], hspace=0.4, wspace=0.3)

    ax1 = fig.add_subplot(gs[0, 0])
    labels = [shorten(p, 22) for p in top_rev.index]
    ax1.barh(labels, top_rev.values, color=COLORS["accent"])
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax1, "Top 10 Products by Revenue")

    ax2 = fig.add_subplot(gs[0, 1])
    labels2 = [shorten(p, 22) for p in top_profit.index]
    ax2.barh(labels2, top_profit.values, color=COLORS["profit"])
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax2, "Top 10 Products by Profit")

    ax3 = fig.add_subplot(gs[1, 0])
    ax3.bar(by_cat.index, by_cat.values, color=COLORS["palette"][:3])
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax3, "Revenue by Category")

    ax4 = fig.add_subplot(gs[1, 1])
    ax4.barh(by_sub.index, by_sub.values, color=COLORS["accent"])
    ax4.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax4, "Revenue by Subcategory (Top 12)")

    ax5 = fig.add_subplot(gs[2, :])
    labels5 = [shorten(p, 28) for p in top_qty.index]
    ax5.barh(labels5, top_qty.values, color="#7C3AED")
    style_axes(ax5, "Quantity Sold by Product (Top 15)")

    out = os.path.join(IMAGES, "product_dashboard.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close(fig)
    return out


def revenue_band(value):
    if value >= 5_000_000:
        return "≥ $5M"
    if value >= 2_000_000:
        return "$2M – $5M"
    if value >= 1_000_000:
        return "$1M – $2M"
    if value >= 500_000:
        return "$500K – $1M"
    return "< $500K"


def build_customer(df):
    cust = (
        df.groupby(["Customer_ID", "Customer_Name"])
        .agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
        .reset_index()
    )
    cust["AOV"] = cust["Revenue"] / cust["Orders"]
    top = cust.nlargest(10, "Revenue").sort_values("Revenue")
    by_seg = df.groupby("Segment")["Sales"].sum()
    top_orders = cust.nlargest(10, "Orders").sort_values("Orders")

    cust["Band"] = cust["Revenue"].apply(revenue_band)
    band_order = ["< $500K", "$500K – $1M", "$1M – $2M", "$2M – $5M", "≥ $5M"]
    band_counts = cust["Band"].value_counts().reindex(band_order).fillna(0)

    fig = plt.figure(figsize=(16, 10), facecolor=COLORS["bg"])
    fig.suptitle("Customer Analysis", fontsize=16, fontweight="700", color=COLORS["text"], x=0.02, y=0.97, ha="left")
    gs = gridspec.GridSpec(3, 2, figure=fig, height_ratios=[1.1, 1, 0.9], hspace=0.45, wspace=0.3)

    ax_table = fig.add_subplot(gs[0, 0])
    ax_table.axis("off")
    style_axes(ax_table, "Top Customers")
    rows = []
    for _, r in top.iterrows():
        rows.append([
            shorten(r["Customer_Name"], 18),
            fmt_currency(r["Revenue"]),
            fmt_currency(r["Profit"]),
            f"{int(r['Orders']):,}",
            fmt_currency(r["AOV"]),
        ])
    table = ax_table.table(
        cellText=rows,
        colLabels=["Customer", "Revenue", "Profit", "Orders", "AOV"],
        loc="center", cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.4)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor(COLORS["accent"])
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor(COLORS["card"])
        cell.set_edgecolor(COLORS["border"])

    ax_seg = fig.add_subplot(gs[0, 1])
    ax_seg.bar(by_seg.index, by_seg.values, color=COLORS["palette"][:3])
    ax_seg.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    style_axes(ax_seg, "Revenue by Segment")

    ax_wf = fig.add_subplot(gs[1, 0])
    cum = top["Revenue"].values
    names = [shorten(n, 16) for n in top["Customer_Name"]]
    running = np.cumsum(cum)
    ax_wf.bar(range(len(cum)), cum, color=COLORS["accent"], label="Customer")
    ax_wf.plot(range(len(cum)), running, color=COLORS["profit"], marker="o", linewidth=1.5, label="Cumulative")
    ax_wf.set_xticks(range(len(cum)))
    ax_wf.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
    ax_wf.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_currency(x)))
    ax_wf.legend(fontsize=8, frameon=False)
    style_axes(ax_wf, "Customer Contribution (Top 10)")

    ax_ord = fig.add_subplot(gs[1, 1])
    ax_ord.barh(
        [shorten(n, 18) for n in top_orders["Customer_Name"]],
        top_orders["Orders"].values,
        color="#D97706",
    )
    style_axes(ax_ord, "Orders by Customer (Top 10)")

    ax_dist = fig.add_subplot(gs[2, :])
    ax_dist.bar(band_counts.index, band_counts.values, color=COLORS["accent"])
    style_axes(ax_dist, "Revenue Distribution (Customer Count by Band)")
    ax_dist.tick_params(axis="x", rotation=15)

    out = os.path.join(IMAGES, "customer_dashboard.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close(fig)
    return out


def main():
    os.makedirs(IMAGES, exist_ok=True)
    df = load()
    for builder in (build_executive, build_product, build_customer):
        print(f"Saved {builder(df)}")


if __name__ == "__main__":
    main()
