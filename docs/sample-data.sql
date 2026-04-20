USE business_db;

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '客户名称',
    region VARCHAR(100) COMMENT '所在区域',
    phone VARCHAR(50) COMMENT '联系电话',
    email VARCHAR(255) COMMENT '邮箱',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) COMMENT='客户信息表';

-- Products
CREATE TABLE IF NOT EXISTS products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '产品名称',
    category VARCHAR(100) COMMENT '产品类别',
    price DECIMAL(10,2) COMMENT '单价',
    stock INT DEFAULT 0 COMMENT '库存数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) COMMENT='产品信息表';

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT NOT NULL COMMENT '客户ID',
    product_id BIGINT NOT NULL COMMENT '产品ID',
    quantity INT NOT NULL COMMENT '数量',
    amount DECIMAL(12,2) NOT NULL COMMENT '订单金额',
    order_date DATE NOT NULL COMMENT '订单日期',
    status ENUM('PENDING','SHIPPED','COMPLETED','CANCELLED') DEFAULT 'PENDING' COMMENT '订单状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
) COMMENT='订单表';

-- Insert sample customers
INSERT INTO customers (name, region, phone, email) VALUES
('北京科技有限公司', '华北', '010-88881234', 'bj@example.com'),
('上海贸易集团', '华东', '021-66661234', 'sh@example.com'),
('广州制造有限公司', '华南', '020-33331234', 'gz@example.com'),
('成都数据科技', '西南', '028-55551234', 'cd@example.com'),
('深圳创新科技', '华南', '0755-22221234', 'sz@example.com'),
('杭州电商有限公司', '华东', '0571-77771234', 'hz@example.com'),
('武汉工程技术', '华中', '027-44441234', 'wh@example.com'),
('南京软件科技', '华东', '025-99991234', 'nj@example.com'),
('西安智能制造', '西北', '029-11111234', 'xa@example.com'),
('重庆物流有限公司', '西南', '023-33331234', 'cq@example.com');

-- Insert sample products
INSERT INTO products (name, category, price, stock) VALUES
('智能服务器 A100', '服务器', 45000.00, 120),
('企业级交换机 S5000', '网络设备', 8500.00, 300),
('云存储模块 CS200', '存储设备', 12000.00, 85),
('安全防火墙 FW300', '安全设备', 25000.00, 60),
('工业传感器 IS50', '物联网', 350.00, 5000),
('数据分析平台 DA Pro', '软件', 180000.00, 999),
('智能摄像头 IC100', '安防设备', 1200.00, 2000),
('无线AP WA600', '网络设备', 650.00, 1500),
('UPS电源 UP3000', '电源设备', 3500.00, 200),
('光纤模块 FM10G', '网络配件', 280.00, 8000);

-- Insert sample orders (spanning multiple months)
INSERT INTO orders (customer_id, product_id, quantity, amount, order_date, status) VALUES
(1, 1, 10, 450000.00, '2026-01-15', 'COMPLETED'),
(1, 6, 2, 360000.00, '2026-01-20', 'COMPLETED'),
(2, 2, 50, 425000.00, '2026-01-25', 'COMPLETED'),
(3, 5, 500, 175000.00, '2026-02-01', 'COMPLETED'),
(2, 3, 20, 240000.00, '2026-02-10', 'COMPLETED'),
(4, 6, 1, 180000.00, '2026-02-15', 'COMPLETED'),
(5, 1, 5, 225000.00, '2026-02-20', 'COMPLETED'),
(6, 7, 200, 240000.00, '2026-03-01', 'COMPLETED'),
(1, 4, 8, 200000.00, '2026-03-05', 'COMPLETED'),
(7, 2, 100, 850000.00, '2026-03-10', 'SHIPPED'),
(3, 1, 15, 675000.00, '2026-03-15', 'SHIPPED'),
(8, 6, 3, 540000.00, '2026-03-18', 'SHIPPED'),
(5, 3, 30, 360000.00, '2026-03-20', 'PENDING'),
(9, 5, 1000, 350000.00, '2026-03-25', 'PENDING'),
(10, 8, 300, 195000.00, '2026-04-01', 'PENDING'),
(2, 1, 20, 900000.00, '2026-04-05', 'PENDING'),
(6, 4, 5, 125000.00, '2026-04-08', 'PENDING'),
(4, 7, 100, 120000.00, '2026-04-10', 'PENDING'),
(1, 9, 30, 105000.00, '2026-04-11', 'PENDING'),
(3, 10, 500, 140000.00, '2026-04-12', 'PENDING');
