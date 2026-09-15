-- Slice + HAVING: เดือนที่มียอดรวมมากกว่า 500 บาท
SELECT month, SUM(amount) AS revenue
FROM sales
GROUP BY month
HAVING SUM(amount) > 500
ORDER BY month;
