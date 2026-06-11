-- Revenue Analysis
-- This script provides revenue performance analysis by geography and time.

-- Revenue by Region
SELECT Region,
       SUM(Sales) AS Total_Revenue,
       SUM(Profit) AS Total_Profit,
       SUM(Quantity) AS Total_Units
FROM Orders
GROUP BY Region
ORDER BY Total_Revenue DESC;

-- Revenue by State
SELECT State,
       Region,
       SUM(Sales) AS Total_Revenue,
       SUM(Profit) AS Total_Profit
FROM Orders
GROUP BY State, Region
ORDER BY Total_Revenue DESC;

-- Monthly Revenue Trend
SELECT DATEPART(YEAR, Order_Date) AS Sales_Year,
       DATEPART(MONTH, Order_Date) AS Sales_Month,
       FORMAT(Order_Date, 'yyyy-MM') AS Month_Label,
       SUM(Sales) AS Monthly_Revenue,
       SUM(Profit) AS Monthly_Profit
FROM Orders
GROUP BY DATEPART(YEAR, Order_Date), DATEPART(MONTH, Order_Date), FORMAT(Order_Date, 'yyyy-MM')
ORDER BY Sales_Year, Sales_Month;

-- Running Revenue Trend using Window Function
SELECT Sales_Year,
       Sales_Month,
       Month_Label,
       Monthly_Revenue,
       SUM(Monthly_Revenue) OVER (ORDER BY Sales_Year, Sales_Month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS Cumulative_Revenue
FROM (
    SELECT DATEPART(YEAR, Order_Date) AS Sales_Year,
           DATEPART(MONTH, Order_Date) AS Sales_Month,
           FORMAT(Order_Date, 'yyyy-MM') AS Month_Label,
           SUM(Sales) AS Monthly_Revenue
    FROM Orders
    GROUP BY DATEPART(YEAR, Order_Date), DATEPART(MONTH, Order_Date), FORMAT(Order_Date, 'yyyy-MM')
) AS MonthlyRevenue
ORDER BY Sales_Year, Sales_Month;
