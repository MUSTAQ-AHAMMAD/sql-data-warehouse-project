-- ============================================
-- Gold Layer Tables - SQL Server
-- ============================================

USE SALLA_DWH;
GO

-- Create Gold schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'gold')
BEGIN
    EXEC('CREATE SCHEMA gold');
END
GO

-- Drop tables if they exist
IF OBJECT_ID('gold.gold_sales_summary', 'U') IS NOT NULL DROP TABLE gold.gold_sales_summary;
IF OBJECT_ID('gold.gold_customer_metrics', 'U') IS NOT NULL DROP TABLE gold.gold_customer_metrics;
IF OBJECT_ID('gold.gold_product_performance', 'U') IS NOT NULL DROP TABLE gold.gold_product_performance;
IF OBJECT_ID('gold.gold_daily_revenue', 'U') IS NOT NULL DROP TABLE gold.gold_daily_revenue;
GO

-- Sales Summary Table
CREATE TABLE gold.gold_sales_summary (
    summary_date DATE PRIMARY KEY,
    total_orders INT,
    total_revenue DECIMAL(15,2),
    total_customers INT,
    average_order_value DECIMAL(15,2),
    total_products_sold INT,
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Customer Metrics Table
CREATE TABLE gold.gold_customer_metrics (
    customer_id INT PRIMARY KEY,
    customer_name NVARCHAR(255),
    email NVARCHAR(255),
    total_orders INT,
    total_spent DECIMAL(15,2),
    average_order_value DECIMAL(15,2),
    first_order_date DATE,
    last_order_date DATE,
    customer_lifetime_days INT,
    is_active BIT,
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Product Performance Table
CREATE TABLE gold.gold_product_performance (
    product_id INT PRIMARY KEY,
    product_name NVARCHAR(255),
    sku NVARCHAR(100),
    category NVARCHAR(100),
    total_orders INT,
    total_quantity_sold INT,
    total_revenue DECIMAL(15,2),
    average_price DECIMAL(15,2),
    current_stock INT,
    is_active BIT,
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Daily Revenue Table
CREATE TABLE gold.gold_daily_revenue (
    revenue_date DATE PRIMARY KEY,
    daily_revenue DECIMAL(15,2),
    order_count INT,
    customer_count INT,
    avg_order_value DECIMAL(15,2),
    payment_method NVARCHAR(50),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create indexes
CREATE INDEX idx_gold_customer_metrics_spent ON gold.gold_customer_metrics(total_spent DESC);
CREATE INDEX idx_gold_customer_metrics_orders ON gold.gold_customer_metrics(total_orders DESC);
CREATE INDEX idx_gold_product_performance_revenue ON gold.gold_product_performance(total_revenue DESC);
CREATE INDEX idx_gold_daily_revenue_date ON gold.gold_daily_revenue(revenue_date DESC);
GO

PRINT '✅ Gold layer tables created successfully';
GO
