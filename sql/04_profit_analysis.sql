-- Profit Analysis
-- This script focuses on profit margin, discount impact, and category profitability.

-- Profit by Category
SELECT Category,
       SUM(Profit) AS Total_Profit,
       SUM(Sales) AS Total_Revenue,
       CASE WHEN SUM(Sales) = 0 THEN 0 ELSE SUM(Profit) * 100.0 / SUM(Sales) END AS Profit_Margin_Percent
FROM Orders
GROUP BY Category
ORDER BY Total_Profit DESC;

-- Monthly Profit Trend
SELECT DATEPART(YEAR, Order_Date) AS Sales_Year,
       DATEPART(MONTH, Order_Date) AS Sales_Month,
       FORMAT(Order_Date, 'yyyy-MM') AS Month_Label,
       SUM(Profit) AS Monthly_Profit
FROM Orders
GROUP BY DATEPART(YEAR, Order_Date), DATEPART(MONTH, Order_Date), FORMAT(Order_Date, 'yyyy-MM')
ORDER BY Sales_Year, Sales_Month;

-- Discount Impact on Margin
SELECT Discount,
       SUM(Sales) AS Revenue,
       SUM(Profit) AS Profit,
       CASE WHEN SUM(Sales) = 0 THEN 0 ELSE SUM(Profit) * 100.0 / SUM(Sales) END AS Margin_Percent
FROM Orders
GROUP BY Discount
ORDER BY Discount;

-- Highly Profitable Products
SELECT TOP 20 Product_Name,
       Category,
       Sub_Category,
       SUM(Sales) AS Revenue,
       SUM(Profit) AS Profit,
       CASE WHEN SUM(Sales) = 0 THEN 0 ELSE SUM(Profit) * 100.0 / SUM(Sales) END AS Profit_Margin_Percent
FROM Orders
GROUP BY Product_Name, Category, Sub_Category
ORDER BY Profit DESC;
