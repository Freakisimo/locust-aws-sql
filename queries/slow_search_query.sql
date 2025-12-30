-- Slow search query: Full text search simulation with sorting and joins
-- This query performs string matching across large sets and joins
SELECT 
    p.name, 
    p.description, 
    c.name as category,
    COUNT(r.id) as review_count,
    AVG(r.rating) as avg_rating
FROM products p
JOIN categories c ON p.category_id = c.id
LEFT JOIN reviews r ON p.id = r.product_id
WHERE p.description LIKE '%product%' 
   OR p.name LIKE '%5%'
GROUP BY p.id, c.id
HAVING AVG(r.rating) > 2
ORDER BY review_count DESC, avg_rating DESC
LIMIT 50;
