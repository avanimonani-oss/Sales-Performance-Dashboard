-- KPI Queries
-- This script produces key performance metrics for executive reporting.

-- Total Revenue
SELECT SUM(Sales) AS Total_Revenue
FROM Orders;

-- Total Profit
SELECT SUM(Profit) AS Total_Profit
FROM Orders;

-- Total Orders
SELECT COUNT(DISTINCT Order_ID) AS Total_Orders
FROM Orders;

-- Average Order Value
SELECT AVG(Order_Value) AS Average_Order_Value
FROM (
    SELECT Order_ID,
           SUM(Sales) AS Order_Value
    FROM Orders
    GROUP BY Order_ID
) AS OrderTotals;

-- Profit Margin Percentage
SELECT CASE WHEN SUM(Sales) = 0 THEN 0 ELSE SUM(Profit) * 100.0 / SUM(Sales) END AS Profit_Margin_Percent
FROM Orders;

-- Customer Count
SELECT COUNT(DISTINCT Customer_ID) AS Customer_Count
FROM Orders;

-- Product Count
SELECT COUNT(DISTINCT Product_Name) AS Product_Count
FROM Orders;

-- Year-Over-Year Revenue Growth
WITH AnnualRevenue AS (
    SELECT DATEPART(YEAR, Order_Date) AS Sales_Year,
           SUM(Sales) AS Revenue
    FROM Orders
    GROUP BY DATEPART(YEAR, Order_Date)
)
SELECT a.Sales_Year,
       a.Revenue,
       b.Revenue AS Prior_Revenue,
       CASE WHEN b.Revenue = 0 THEN NULL ELSE (a.Revenue - b.Revenue) * 100.0 / b.Revenue END AS Revenue_Growth_Percent
FROM AnnualRevenue a
LEFT JOIN AnnualRevenue b
    ON a.Sales_Year = b.Sales_Year + 1
ORDER BY a.Sales_Year;
