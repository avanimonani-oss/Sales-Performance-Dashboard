-- Customer Analysis
-- This script covers high-value customers, segmentation, and order behavior.

-- Top 10 Customers by Revenue
SELECT TOP 10 Customer_ID,
       Customer_Name,
       SUM(Sales) AS Total_Revenue,
       SUM(Profit) AS Total_Profit,
       COUNT(DISTINCT Order_ID) AS Total_Orders,
       AVG(Sales) AS Avg_Line_Item_Sales
FROM Orders
GROUP BY Customer_ID, Customer_Name
ORDER BY Total_Revenue DESC;

-- Customer Segmentation Overview
SELECT Segment,
       COUNT(DISTINCT Customer_ID) AS Customer_Count,
       SUM(Sales) AS Segment_Revenue,
       SUM(Profit) AS Segment_Profit,
       AVG(Sales) AS Avg_Sales_Per_Line_Item
FROM Orders
GROUP BY Segment
ORDER BY Segment_Revenue DESC;

-- Repeat Customer Rate using CTE
WITH CustomerOrders AS (
    SELECT Customer_ID,
           COUNT(DISTINCT Order_ID) AS Orders_Per_Customer
    FROM Orders
    GROUP BY Customer_ID
)
SELECT COUNT(*) AS Total_Customers,
       SUM(CASE WHEN Orders_Per_Customer > 1 THEN 1 ELSE 0 END) AS Repeat_Customers,
       CAST(SUM(CASE WHEN Orders_Per_Customer > 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 AS Repeat_Customer_Percentage
FROM CustomerOrders;

-- High-Value Customer Contribution
SELECT TOP 10 Customer_ID,
       Customer_Name,
       SUM(Sales) AS Total_Revenue,
       SUM(Profit) AS Total_Profit,
       SUM(Sales) * 100.0 / SUM(SUM(Sales)) OVER () AS Revenue_Share_Percent
FROM Orders
GROUP BY Customer_ID, Customer_Name
ORDER BY Total_Revenue DESC;
