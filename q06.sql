-- Dice: กรองทั้งจังหวัด Bangkok และหมวด Drink
SELECT month, SUM(amount) AS revenue
FROM sales
WHERE province = 'Bangkok' AND category = 'Drink'
GROUP BY month
ORDER BY month;
