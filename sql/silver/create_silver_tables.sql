-- ============================================
-- Silver Layer Tables - SQL Server
-- ============================================

USE SALLA_DWH;
GO

-- Create Silver schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'silver')
BEGIN
    EXEC('CREATE SCHEMA silver');
END
GO

-- Drop tables if they exist
IF OBJECT_ID('silver.silver_orders', 'U') IS NOT NULL DROP TABLE silver.silver_orders;
IF OBJECT_ID('silver.silver_customers', 'U') IS NOT NULL DROP TABLE silver.silver_customers;
IF OBJECT_ID('silver.silver_products', 'U') IS NOT NULL DROP TABLE silver.silver_products;
GO

-- Create Silver Orders Table
CREATE TABLE silver.silver_orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_number NVARCHAR(50),
    order_date DATE,
    order_time TIME,
    status NVARCHAR(50),
    payment_method NVARCHAR(50),
    shipping_method NVARCHAR(50),
    subtotal DECIMAL(15,2),
    tax DECIMAL(15,2),
    shipping_cost DECIMAL(15,2),
    discount DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    currency NVARCHAR(10),
    notes NVARCHAR(MAX),
    processed_at DATETIME2 DEFAULT GETDATE(),
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create Silver Customers Table
CREATE TABLE silver.silver_customers (
    customer_id INT PRIMARY KEY,
    first_name NVARCHAR(100),
    last_name NVARCHAR(100),
    email NVARCHAR(255),
    phone NVARCHAR(50),
    country NVARCHAR(100),
    city NVARCHAR(100),
    address NVARCHAR(500),
    postal_code NVARCHAR(20),
    customer_type NVARCHAR(50),
    registration_date DATE,
    is_active BIT DEFAULT 1,
    processed_at DATETIME2 DEFAULT GETDATE(),
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create Silver Products Table
CREATE TABLE silver.silver_products (
    product_id INT PRIMARY KEY,
    product_name NVARCHAR(255),
    sku NVARCHAR(100),
    description NVARCHAR(MAX),
    category NVARCHAR(100),
    brand NVARCHAR(100),
    price DECIMAL(15,2),
    cost DECIMAL(15,2),
    currency NVARCHAR(10),
    stock_quantity INT,
    is_active BIT DEFAULT 1,
    weight DECIMAL(10,2),
    dimensions NVARCHAR(100),
    processed_at DATETIME2 DEFAULT GETDATE(),
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create indexes
CREATE INDEX idx_silver_orders_customer ON silver.silver_orders(customer_id);
CREATE INDEX idx_silver_orders_date ON silver.silver_orders(order_date);
CREATE INDEX idx_silver_orders_status ON silver.silver_orders(status);
CREATE INDEX idx_silver_customers_email ON silver.silver_customers(email);
CREATE INDEX idx_silver_products_sku ON silver.silver_products(sku);
GO

PRINT '✅ Silver layer tables created successfully';
GO
