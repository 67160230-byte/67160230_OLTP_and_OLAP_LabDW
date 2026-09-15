-- Drill-down: ยอดรายวันในเดือนกันยายน
SELECT full_date, province, SUM(amount) AS revenue
FROM sales
WHERE month = '2026-09'
GROUP BY full_date, province
ORDER BY full_date, province;
