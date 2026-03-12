INSERT INTO books (isbn, title, author, genre, price, stock) VALUES
('978-0132350884', 'Clean Code',                        'Robert C. Martin',    'Software',   39.99, 10),
('978-0201616224', 'The Pragmatic Programmer',           'Andrew Hunt',         'Software',   44.99,  5),
('978-0201633610', 'Design Patterns',                    'Erich Gamma',         'Software',   49.99,  7),
('978-0201485677', 'Refactoring',                        'Martin Fowler',       'Software',   46.99,  3),
('978-0262035613', 'Deep Learning',                      'Ian Goodfellow',      'AI/ML',      59.99,  4),
('978-0358012573', 'AI Superpowers',                     'Kai-Fu Lee',          'AI/ML',      34.99,  6),
('978-1593279288', 'Python Crash Course',                'Eric Matthes',        'Programming', 29.99, 8),
('978-1492032649', 'Hands-On Machine Learning',          'Aurélien Géron',      'AI/ML',      54.99,  5),
('978-0201835953', 'The Mythical Man-Month',             'Frederick P. Brooks', 'Software',   31.99,  2),
('978-0262510875', 'Structure and Interpretation',       'Harold Abelson',      'CS',         51.99,  4);

INSERT INTO customers (id, name, email, phone) VALUES
(1, 'Ali Ahmad',    'ali@email.com',    '+966500000001'),
(2, 'Sara Nasser',  'sara@email.com',   '+966500000002'),
(3, 'Omar Khalid',  'omar@email.com',   '+966500000003'),
(4, 'Lina Yousef',  'lina@email.com',   '+966500000004'),
(5, 'Adam Saleh',   'adam@email.com',    '+966500000005'),
(6, 'Noor Faisal',  'noor@email.com',   '+966500000006');

INSERT INTO orders (id, customer_id, order_date, status) VALUES
(1, 1, '2026-03-01', 'completed'),
(2, 2, '2026-03-05', 'completed'),
(3, 3, '2026-03-08', 'completed'),
(4, 5, '2026-03-10', 'completed');

INSERT INTO order_items (order_id, isbn, quantity, unit_price) VALUES
(1, '978-0132350884', 2, 39.99),
(1, '978-1593279288', 1, 29.99),
(2, '978-0201616224', 1, 44.99),
(2, '978-0262035613', 1, 59.99),
(3, '978-0201633610', 1, 49.99),
(3, '978-0201485677', 2, 46.99),
(4, '978-1492032649', 1, 54.99);