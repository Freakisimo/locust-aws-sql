-- Complex analytic query: Sales per category, average rating and stock status
-- This query involves multiple joins, aggregations and ranking
WITH category_performance AS (
    SELECT 
        c.name as category_name,
        SUM(o.amount) as total_sales,
        COUNT(DISTINCT o.order_id) as order_count,
        AVG(r.rating) as avg_rating
    FROM categories c
    JOIN products p ON c.id = p.category_id
    LEFT JOIN orders o ON p.id = o.user_id -- (Simulated join just for complexity)
    LEFT JOIN reviews r ON p.id = r.product_id
    GROUP BY c.name
)
SELECT 
    cp.*,
    RANK() OVER (ORDER BY total_sales DESC) as sales_rank
FROM category_performance cp
ORDER BY total_sales DESC;
