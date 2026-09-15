-- Drill-down: ยอดขายรายวัน (ลงรายละเอียดเวลา)
SELECT full_date, SUM(amount) AS revenue
FROM sales
GROUP BY full_date
ORDER BY full_date;
