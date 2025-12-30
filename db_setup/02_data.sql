INSERT INTO users (name, email) VALUES
('John Doe', 'john.doe@example.com'),
('Jane Smith', 'jane.smith@example.com'),
('Peter Jones', 'peter.jones@example.com');

INSERT INTO orders (user_id, order_date, amount) VALUES
(1, '2025-10-15', 100.50),
(1, '2025-10-14', 75.20),
(2, '2025-10-13', 200.00),
(3, '2025-10-15', 50.00);
