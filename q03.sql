-- Roll-up: ยอดขายรวมตามจังหวัดและเดือน
SELECT province, month, SUM(amount) AS revenue
FROM sales
GROUP BY province, month
ORDER BY province, month;
