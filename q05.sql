-- Slice: กรองเฉพาะเดือนกันยายน
SELECT product_name, SUM(amount) AS revenue
FROM sales
WHERE month = '2026-09'
GROUP BY product_name
ORDER BY revenue DESC;
