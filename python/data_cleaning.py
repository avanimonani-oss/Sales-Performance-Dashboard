import csv
import math
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

ORDER_COUNT = 50000
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data")
RAW_FILE = os.path.join(DATA_PATH, "sales_data.csv")
CLEAN_FILE = os.path.join(DATA_PATH, "sales_data_cleaned.csv")

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
REGIONS = ["East", "West", "Central", "South", "North"]
STATES_BY_REGION = {
    "East": ["New York", "Pennsylvania", "New Jersey", "Massachusetts"],
    "West": ["California", "Washington", "Oregon", "Nevada"],
    "Central": ["Texas", "Illinois", "Ohio", "Michigan"],
    "South": ["Florida", "Georgia", "Virginia", "North Carolina"],
    "North": ["Colorado", "Minnesota", "Wisconsin", "Indiana"]
}
CITIES = [
    "New York", "Philadelphia", "Boston", "Los Angeles", "San Francisco", "Seattle", "Portland", "Las Vegas",
    "Dallas", "Chicago", "Houston", "Atlanta", "Miami", "Orlando", "Denver", "Minneapolis", "Madison",
    "Indianapolis", "Cleveland", "Columbus"
]
PRODUCT_CATALOG = {
    "Technology": {
        "Phones": ["iPhone 13", "Samsung Galaxy S22", "Google Pixel 6", "Desk Phone"],
        "Accessories": ["Wireless Mouse", "Noise Cancelling Headset", "HD Webcam", "Laptop Stand"],
        "Machines": ["Laser Printer", "Inkjet Printer", "Desktop PC", "Server Rack"]
    },
    "Furniture": {
        "Chairs": ["Executive Chair", "Conference Chair", "Ergonomic Task Chair", "Gaming Chair"],
        "Tables": ["Conference Table", "Office Desk", "Laptop Table", "Folding Table"],
        "Storage": ["Filing Cabinet", "Metal Cabinet", "Bookshelf", "Storage Shelves"],
        "Bookcases": ["Ikea Bookcase", "Wooden Bookcase", "Glass Bookcase", "Modular Shelving"]
    },
    "Office Supplies": {
        "Binders": ["Acco Binder", "Plastic Binder", "Ring Binder", "Presentation Binder"],
        "Paper": ["Printer Paper", "Legal Pads", "Notebooks", "Sticky Notes"],
        "Art": ["Sketchbook", "Markers", "Colored Pencils", "Canvas Pack"],
        "Labels": ["Label Holder", "Name Tags", "Shipping Labels", "Folder Labels"]
    }
}
CUSTOMERS = [
    ("CUST-{:03d}".format(i + 1), name)
    for i, name in enumerate([
        "Claire Gute", "Reginald Hill", "Edward Bowker", "Andrew Allen", "Carla Cox", "Linda Ross",
        "James Brown", "Melissa Martin", "Susan Howard", "Michael Brown", "Lily Peterson", "Yvonne King",
        "Patricia Taylor", "Jackie King", "Matthew Moore", "Tina Vaughn", "Brian White", "Beth Clark",
        "Daniel Edge", "Emily Davis", "Oliver Chen", "Grace Lee", "Natalie Kim", "Henry Scott",
        "Ava Brooks", "Sophia Martin", "Noah Johnson", "Mia Clark", "Ethan Davis", "Amelia Rogers"
    ])
]
HEADERS = [
    "Order_ID", "Order_Date", "Customer_ID", "Customer_Name", "Segment", "Region", "State", "City",
    "Category", "Sub_Category", "Product_Name", "Sales", "Quantity", "Discount", "Profit"
]


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def build_order_id(index):
    prefix = random.choice(["CA", "US", "EU"])
    return f"{prefix}-{2024 - (index % 5)}-{100000 + index}"


def calculate_profit(sales, category, discount):
    margin = {"Technology": 0.28, "Furniture": 0.20, "Office Supplies": 0.14}
    base_profit = sales * margin.get(category, 0.16)
    penalty = sales * discount * 0.35
    return round(base_profit - penalty, 2)


def generate_sales_data(rows=ORDER_COUNT):
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2024, 12, 31)
    records = []

    for i in range(rows):
        order_id = build_order_id(i)
        order_date = random_date(start_date, end_date).date().isoformat()
        customer_id, customer_name = random.choice(CUSTOMERS)
        segment = random.choice(SEGMENTS)
        region = random.choice(REGIONS)
        state = random.choice(STATES_BY_REGION[region])
        city = random.choice(CITIES)
        category = random.choice(list(PRODUCT_CATALOG.keys()))
        sub_category = random.choice(list(PRODUCT_CATALOG[category].keys()))
        product_name = random.choice(PRODUCT_CATALOG[category][sub_category])
        quantity = random.randint(1, 8)
        unit_price = round(random.uniform(8.0, 1200.0), 2)
        discount = round(random.choice([0.0, 0.05, 0.1, 0.15, 0.2]), 2)
        sales = round(unit_price * quantity * (1 - discount), 2)
        profit = calculate_profit(sales, category, discount)

        records.append([
            order_id,
            order_date,
            customer_id,
            customer_name,
            segment,
            region,
            state,
            city,
            category,
            sub_category,
            product_name,
            sales,
            quantity,
            discount,
            profit
        ])

    os.makedirs(DATA_PATH, exist_ok=True)
    with open(RAW_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADERS)
        writer.writerows(records)
    print(f"Generated raw dataset at {RAW_FILE} with {rows} rows.")


def clean_sales_data():
    df = pd.read_csv(RAW_FILE)

    df.columns = [col.strip() for col in df.columns]
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df["Customer_ID"] = df["Customer_ID"].astype(str).str.strip()
    df["Customer_Name"] = df["Customer_Name"].astype(str).str.strip()
    df["Segment"] = df["Segment"].astype(str).str.title().replace("Nan", "Unknown")
    df["Region"] = df["Region"].astype(str).str.title().replace("Nan", "Unknown")
    df["State"] = df["State"].astype(str).str.title().replace("Nan", "Unknown")
    df["City"] = df["City"].astype(str).str.title().replace("Nan", "Unknown")
    df["Category"] = df["Category"].astype(str).str.title().replace("Nan", "Unknown")
    df["Sub_Category"] = df["Sub_Category"].astype(str).str.title().replace("Nan", "Unknown")
    df["Product_Name"] = df["Product_Name"].astype(str).str.strip()

    numeric_cols = ["Sales", "Quantity", "Discount", "Profit"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Sales"] = df["Sales"].fillna(0.0).round(2)
    df["Quantity"] = df["Quantity"].fillna(1).astype(int)
    df["Discount"] = df["Discount"].fillna(0.0).round(2)
    df["Profit"] = df["Profit"].fillna(df["Sales"] * 0.15).round(2)

    df = df.drop_duplicates()
    df = df.dropna(subset=["Order_ID", "Order_Date", "Customer_ID"])

    df["Order_Year"] = df["Order_Date"].dt.year
    df["Order_Month"] = df["Order_Date"].dt.month
    df["Order_Month_Name"] = df["Order_Date"].dt.strftime("%b")

    df.loc[df["Profit"] > df["Sales"], "Profit"] = df["Sales"] * 0.32
    df.loc[df["Profit"] < -df["Sales"], "Profit"] = df["Sales"] * 0.05

    df.to_csv(CLEAN_FILE, index=False)
    print(f"Saved cleaned dataset at {CLEAN_FILE} with {len(df)} rows.")


if __name__ == "__main__":
    random.seed(2026)
    generate_sales_data()
    clean_sales_data()
