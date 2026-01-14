-- Bronze Layer Schema for SQL Server: Raw data from Salla API
-- This layer stores data as close to the source as possible

-- Create database (run separately if needed)
-- CREATE DATABASE SALLA_DWH;
-- GO

USE SALLA_DWH;
GO

-- Create Bronze schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'bronze')
BEGIN
    EXEC('CREATE SCHEMA bronze');
END
GO

-- Bronze Orders Table
-- Stores raw order data from Salla API
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'bronze_orders' AND schema_id = SCHEMA_ID('bronze'))
BEGIN
    CREATE TABLE bronze.bronze_orders (
        id BIGINT PRIMARY KEY,
        reference_id VARCHAR(100),
        status VARCHAR(50),
        amount FLOAT,
        currency VARCHAR(10),
        customer_id BIGINT,
        customer_name NVARCHAR(255),
        customer_email NVARCHAR(255),
        customer_mobile VARCHAR(50),
        payment_method VARCHAR(100),
        shipping_method VARCHAR(100),
        shipping_address NVARCHAR(MAX), -- JSON stored as text
        items NVARCHAR(MAX), -- JSON stored as text
        created_at DATETIME2,
        updated_at DATETIME2,
        notes NVARCHAR(1000),
        coupon_code VARCHAR(100),
        discount_amount FLOAT,
        tax_amount FLOAT,
        shipping_cost FLOAT,
        total_amount FLOAT,
        loaded_at DATETIME2 DEFAULT GETDATE(),
        source_system VARCHAR(50) DEFAULT 'SALLA_API'
    );
    
    -- Create indexes
    CREATE INDEX idx_bronze_orders_customer ON bronze.bronze_orders(customer_id);
    CREATE INDEX idx_bronze_orders_created ON bronze.bronze_orders(created_at);
    CREATE INDEX idx_bronze_orders_status ON bronze.bronze_orders(status);
END
GO

-- Bronze Customers Table
-- Stores raw customer data from Salla API
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'bronze_customers' AND schema_id = SCHEMA_ID('bronze'))
BEGIN
    CREATE TABLE bronze.bronze_customers (
        id BIGINT PRIMARY KEY,
        first_name NVARCHAR(255),
        last_name NVARCHAR(255),
        email NVARCHAR(255),
        mobile VARCHAR(50),
        mobile_code VARCHAR(10),
        country NVARCHAR(100),
        city NVARCHAR(100),
        gender VARCHAR(20),
        birthday DATE,
        avatar NVARCHAR(500),
        addresses NVARCHAR(MAX), -- JSON stored as text
        created_at DATETIME2,
        updated_at DATETIME2,
        status VARCHAR(50),
        notes NVARCHAR(1000),
        loaded_at DATETIME2 DEFAULT GETDATE(),
        source_system VARCHAR(50) DEFAULT 'SALLA_API'
    );
    
    -- Create indexes
    CREATE INDEX idx_bronze_customers_email ON bronze.bronze_customers(email);
    CREATE INDEX idx_bronze_customers_created ON bronze.bronze_customers(created_at);
END
GO

-- Bronze Products Table
-- Stores raw product data from Salla API
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'bronze_products' AND schema_id = SCHEMA_ID('bronze'))
BEGIN
    CREATE TABLE bronze.bronze_products (
        id BIGINT PRIMARY KEY,
        name NVARCHAR(500),
        description NVARCHAR(MAX),
        price FLOAT,
        sale_price FLOAT,
        cost_price FLOAT,
        sku VARCHAR(100),
        quantity INT,
        unlimited_quantity BIT,
        status VARCHAR(50),
        type VARCHAR(50),
        weight FLOAT,
        weight_unit VARCHAR(20),
        images NVARCHAR(MAX), -- JSON stored as text
        categories NVARCHAR(MAX), -- JSON stored as text
        options NVARCHAR(MAX), -- JSON stored as text
        metadata_title NVARCHAR(500),
        metadata_description NVARCHAR(1000),
        created_at DATETIME2,
        updated_at DATETIME2,
        with_tax BIT,
        is_taxable BIT,
        require_shipping BIT,
        loaded_at DATETIME2 DEFAULT GETDATE(),
        source_system VARCHAR(50) DEFAULT 'SALLA_API'
    );
    
    -- Create indexes
    CREATE INDEX idx_bronze_products_sku ON bronze.bronze_products(sku);
    CREATE INDEX idx_bronze_products_status ON bronze.bronze_products(status);
    CREATE INDEX idx_bronze_products_created ON bronze.bronze_products(created_at);
END
GO

PRINT 'Bronze layer tables created successfully';
