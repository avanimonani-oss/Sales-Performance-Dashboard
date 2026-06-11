import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "images")
CLEAN_FILE = os.path.join(DATA_DIR, "sales_data_cleaned.csv")

sns.set(style="whitegrid", palette="muted")


def load_data():
    if not os.path.exists(CLEAN_FILE):
        raise FileNotFoundError(f"Cleaned dataset not found: {CLEAN_FILE}")
    return pd.read_csv(CLEAN_FILE, parse_dates=["Order_Date"])


def revenue_trend(df):
    revenue = (
        df.groupby([df["Order_Date"].dt.to_period("M")])["Sales"]
        .sum()
        .reset_index()
    )
    revenue["Order_Date"] = revenue["Order_Date"].dt.to_timestamp()

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=revenue, x="Order_Date", y="Sales", marker="o")
    plt.title("Monthly Revenue Trend")
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "eda_monthly_revenue_trend.png"))
    plt.close()


def profit_trend(df):
    profit = (
        df.groupby([df["Order_Date"].dt.to_period("M")])["Profit"]
        .sum()
        .reset_index()
    )
    profit["Order_Date"] = profit["Order_Date"].dt.to_timestamp()

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=profit, x="Order_Date", y="Profit", marker="o", color="#2a9d8f")
    plt.title("Monthly Profit Trend")
    plt.xlabel("Month")
    plt.ylabel("Profit")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "eda_monthly_profit_trend.png"))
    plt.close()


def customer_analysis(df):
    top_customers = (
        df.groupby("Customer_Name")["Sales"]
        .sum()
        .nlargest(10)
        .reset_index()
    )

    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_customers, x="Sales", y="Customer_Name", color="#4c78a8")
    plt.title("Top 10 Customers by Revenue")
    plt.xlabel("Revenue")
    plt.ylabel("Customer")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "eda_top_customers.png"))
    plt.close()


def product_analysis(df):
    top_products = (
        df.groupby("Product_Name")["Sales"]
        .sum()
        .nlargest(10)
        .reset_index()
    )

    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_products, x="Sales", y="Product_Name", color="#f28e2b")
    plt.title("Top 10 Products by Revenue")
    plt.xlabel("Revenue")
    plt.ylabel("Product")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "eda_top_products.png"))
    plt.close()


def regional_analysis(df):
    region_perf = (
        df.groupby("Region")[['Sales', 'Profit']]
        .sum()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax2 = ax.twinx()
    sns.barplot(data=region_perf, x="Region", y="Sales", ax=ax, color="#4c78a8")
    sns.lineplot(data=region_perf, x="Region", y="Profit", marker="o", color="#264653", ax=ax2)
    ax.set_title("Revenue and Profit by Region")
    ax.set_xlabel("Region")
    ax.set_ylabel("Revenue")
    ax2.set_ylabel("Profit")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "eda_region_performance.png"))
    plt.close()


def run_eda():
    df = load_data()
    revenue_trend(df)
    profit_trend(df)
    customer_analysis(df)
    product_analysis(df)
    regional_analysis(df)
    print("EDA visualizations generated in the images folder.")


if __name__ == "__main__":
    os.makedirs(IMAGES_DIR, exist_ok=True)
    run_eda()
