-- Seed categories
INSERT INTO categories (name, description) VALUES
    ('Electronics', 'Devices, gadgets, and tech'),
    ('Books', 'Fiction, non-fiction, and textbooks'),
    ('Clothing', 'Apparel and accessories'),
    ('Home & Kitchen', 'Home appliances and kitchenware'),
    ('Sports', 'Outdoor and indoor sports equipment')
ON CONFLICT DO NOTHING;

-- Seed 1000 users
INSERT INTO users (name, email)
SELECT 
    'User ' || i, 
    'user' || i || '@example.com'
FROM generate_series(4, 1000) AS i
ON CONFLICT (email) DO NOTHING;

-- Seed 500 products
INSERT INTO products (category_id, name, description, price, stock_quantity)
SELECT 
    (i % 5) + 1,
    'Product ' || i,
    'Description for product ' || i,
    (random() * 500 + 10)::numeric(10,2),
    (random() * 100)::integer
FROM generate_series(1, 500) AS i;

-- Seed 5000 orders
INSERT INTO orders (user_id, order_date, amount)
SELECT 
    (random() * 999 + 1)::integer,
    CURRENT_DATE - (random() * 365)::integer * INTERVAL '1 day',
    (random() * 1000 + 5)::numeric(10,2)
FROM generate_series(1, 5000) AS i;

-- Seed 3000 reviews
INSERT INTO reviews (product_id, user_id, rating, comment)
SELECT 
    (random() * 499 + 1)::integer,
    (random() * 999 + 1)::integer,
    (random() * 4 + 1)::integer,
    'Great product! Review number ' || i
FROM generate_series(1, 3000) AS i;
