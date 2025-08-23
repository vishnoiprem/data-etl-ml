CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO orders (user_id, amount) VALUES
('user1', 50.00),
('user2', 75.00);
