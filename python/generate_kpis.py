import os

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CLEAN_FILE = os.path.join(DATA_DIR, "sales_data_cleaned.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "kpis_summary.csv")


def load_data():
    return pd.read_csv(CLEAN_FILE, parse_dates=["Order_Date"])


def calculate_kpis(df):
    kpis = {
        "Total Revenue": df["Sales"].sum(),
        "Total Profit": df["Profit"].sum(),
        "Total Orders": df["Order_ID"].nunique(),
        "Average Order Value": df.groupby("Order_ID")["Sales"].sum().mean(),
        "Profit Margin %": df["Profit"].sum() / df["Sales"].sum() * 100,
        "Customer Count": df["Customer_ID"].nunique(),
        "Product Count": df["Product_Name"].nunique()
    }
    return kpis


def top_customers(df, n=10):
    customer_orders = df.groupby("Customer_ID")["Order_ID"].nunique()
    summary = df.groupby(["Customer_ID", "Customer_Name"])[["Sales", "Profit"]].sum().reset_index()
    summary["Average_Order_Value"] = summary.apply(
        lambda row: row["Sales"] / customer_orders.loc[row["Customer_ID"]],
        axis=1
    )
    return summary.sort_values("Sales", ascending=False).head(n)


def top_products(df, n=10):
    return (
        df.groupby(["Product_Name", "Category", "Sub_Category"])[["Sales", "Profit"]]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(n)
        .reset_index()
    )


def export_kpis(df, kpis):
    summary = pd.DataFrame(list(kpis.items()), columns=["KPI", "Value"])
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved KPI summary to {OUTPUT_FILE}")


def main():
    df = load_data()
    kpis = calculate_kpis(df)
    export_kpis(df, kpis)
    print("KPI Summary")
    for metric, value in kpis.items():
        print(f"{metric}: {value:,.2f}" if isinstance(value, float) else f"{metric}: {value}")
    print("\nTop 10 Customers")
    print(top_customers(df).to_string(index=False))
    print("\nTop 10 Products")
    print(top_products(df).to_string(index=False))


if __name__ == "__main__":
    main()
