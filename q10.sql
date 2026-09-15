-- AOV และค่าเฉลี่ยต่อรายการ
SELECT SUM(amount) AS revenue,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(1.0 * SUM(amount) / COUNT(DISTINCT order_id), 2) AS aov,
       ROUND(1.0 * SUM(amount) / COUNT(*), 2) AS avg_line
FROM sales;
