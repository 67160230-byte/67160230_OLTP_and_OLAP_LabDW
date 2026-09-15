-- UNION ALL: ยอดรายเดือน + แถวรวม ALL
SELECT month AS label, SUM(amount) AS revenue
FROM sales
GROUP BY month
UNION ALL
SELECT 'ALL', SUM(amount)
FROM sales
ORDER BY label;
