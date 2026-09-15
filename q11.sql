-- เทียบจำนวนแถวและยอดรวม ก่อน JOIN (fact_sales) กับหลัง JOIN (sales)
SELECT 'fact_sales' AS source,
       COUNT(*) AS row_count,
       SUM(quantity * unit_price) AS total_amount
FROM fact_sales
UNION ALL
SELECT 'sales',
       COUNT(*),
       SUM(amount)
FROM sales;
