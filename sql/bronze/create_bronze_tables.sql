-- ============================================
-- Bronze Layer Tables - SQL Server
-- ============================================

-- Use the database
USE SALLA_DWH;
GO

-- Create Bronze schema if not exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'bronze')
BEGIN
    EXEC('CREATE SCHEMA bronze');
END
GO

-- Drop tables if they exist (for clean setup)
IF OBJECT_ID('bronze.bronze_orders', 'U') IS NOT NULL DROP TABLE bronze.bronze_orders;
IF OBJECT_ID('bronze.bronze_customers', 'U') IS NOT NULL DROP TABLE bronze.bronze_customers;
IF OBJECT_ID('bronze.bronze_products', 'U') IS NOT NULL DROP TABLE bronze.bronze_products;
GO

-- Create Bronze Orders Table
CREATE TABLE bronze.bronze_orders (
    order_id INT PRIMARY KEY,
    raw_data NVARCHAR(MAX),
    api_response NVARCHAR(MAX),
    source_system NVARCHAR(50) DEFAULT 'salla',
    extracted_at DATETIME2 DEFAULT GETDATE(),
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create Bronze Customers Table
CREATE TABLE bronze.bronze_customers (
    customer_id INT PRIMARY KEY,
    raw_data NVARCHAR(MAX),
    api_response NVARCHAR(MAX),
    source_system NVARCHAR(50) DEFAULT 'salla',
    extracted_at DATETIME2 DEFAULT GETDATE(),
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create Bronze Products Table
CREATE TABLE bronze.bronze_products (
    product_id INT PRIMARY KEY,
    raw_data NVARCHAR(MAX),
    api_response NVARCHAR(MAX),
    source_system NVARCHAR(50) DEFAULT 'salla',
    extracted_at DATETIME2 DEFAULT GETDATE(),
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create indexes
CREATE INDEX idx_bronze_orders_extracted ON bronze.bronze_orders(extracted_at);
CREATE INDEX idx_bronze_customers_extracted ON bronze.bronze_customers(extracted_at);
CREATE INDEX idx_bronze_products_extracted ON bronze.bronze_products(extracted_at);
GO

PRINT '✅ Bronze layer tables created successfully';
GO
