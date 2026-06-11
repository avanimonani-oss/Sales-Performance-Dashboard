-- Product Analysis
-- This script evaluates product performance across categories and subcategories.

-- Top 10 Products by Revenue
SELECT TOP 10 Product_Name,
       Category,
       Sub_Category,
       SUM(Sales) AS Total_Revenue,
       SUM(Profit) AS Total_Profit,
       SUM(Quantity) AS Units_Sold
FROM Orders
GROUP BY Product_Name, Category, Sub_Category
ORDER BY Total_Revenue DESC;

-- Revenue by Category
SELECT Category,
       SUM(Sales) AS Total_Revenue,
       SUM(Profit) AS Total_Profit,
       SUM(Quantity) AS Units_Sold
FROM Orders
GROUP BY Category
ORDER BY Total_Revenue DESC;

-- Subcategory Performance
SELECT Category,
       Sub_Category,
       SUM(Sales) AS Subcategory_Revenue,
       SUM(Profit) AS Subcategory_Profit,
       SUM(Quantity) AS Units_Sold
FROM Orders
GROUP BY Category, Sub_Category
ORDER BY Subcategory_Revenue DESC;

-- Profit by Product with Category Hierarchy
SELECT Category,
       Sub_Category,
       Product_Name,
       SUM(Sales) AS Total_Revenue,
       SUM(Profit) AS Total_Profit,
       CASE WHEN SUM(Sales) = 0 THEN 0 ELSE SUM(Profit) * 100.0 / SUM(Sales) END AS Profit_Margin_Percent
FROM Orders
GROUP BY Category, Sub_Category, Product_Name
ORDER BY Total_Profit DESC;
