-- Roll-up: ยอดขายรวมตามเดือน
SELECT month, SUM(amount) AS revenue
FROM sales
GROUP BY month
ORDER BY month;
