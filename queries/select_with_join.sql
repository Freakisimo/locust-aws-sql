SELECT u.id, u.name, o.order_date
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.id = 1;