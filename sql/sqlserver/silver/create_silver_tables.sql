-- Silver Layer Schema for SQL Server: Cleaned and enriched data
-- This layer contains validated, deduplicated, and standardized data

USE SALLA_DWH;
GO

-- Create Silver schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'silver')
BEGIN
    EXEC('CREATE SCHEMA silver');
END
GO

-- Silver Orders Table
-- Cleaned and enriched order data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'silver_orders' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.silver_orders (
        order_id BIGINT PRIMARY KEY,
        reference_id VARCHAR(100),
        order_status VARCHAR(50),
        order_date DATETIME2,
        customer_id BIGINT,
        customer_name NVARCHAR(255),
        customer_email NVARCHAR(255),
        customer_mobile VARCHAR(50),
        payment_method VARCHAR(100),
        shipping_method VARCHAR(100),
        
        -- Address fields (extracted from JSON)
        shipping_country NVARCHAR(100),
        shipping_city NVARCHAR(100),
        shipping_address_line NVARCHAR(500),
        shipping_postal_code VARCHAR(20),
        
        -- Financial fields
        subtotal_amount FLOAT,
        discount_amount FLOAT,
        tax_amount FLOAT,
        shipping_cost FLOAT,
        total_amount FLOAT,
        currency VARCHAR(10),
        
        -- Metadata
        coupon_code VARCHAR(100),
        notes NVARCHAR(1000),
        items_count INT,
        
        -- Audit fields
        created_at DATETIME2,
        updated_at DATETIME2,
        processed_at DATETIME2 DEFAULT GETDATE()
    );
    
    -- Create indexes
    CREATE INDEX idx_silver_orders_customer ON silver.silver_orders(customer_id);
    CREATE INDEX idx_silver_orders_date ON silver.silver_orders(order_date);
    CREATE INDEX idx_silver_orders_status ON silver.silver_orders(order_status);
END
GO

-- Silver Customers Table
-- Cleaned and enriched customer data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'silver_customers' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.silver_customers (
        customer_id BIGINT PRIMARY KEY,
        full_name NVARCHAR(500),
        first_name NVARCHAR(255),
        last_name NVARCHAR(255),
        email NVARCHAR(255),
        mobile VARCHAR(50),
        mobile_code VARCHAR(10),
        
        -- Location fields
        country NVARCHAR(100),
        city NVARCHAR(100),
        
        -- Demographics
        gender VARCHAR(20),
        birthday DATE,
        age_group VARCHAR(50),
        
        -- Status
        customer_status VARCHAR(50),
        
        -- Metadata
        avatar_url NVARCHAR(500),
        registration_date DATETIME2,
        last_updated DATETIME2,
        processed_at DATETIME2 DEFAULT GETDATE()
    );
    
    -- Create indexes
    CREATE INDEX idx_silver_customers_email ON silver.silver_customers(email);
    CREATE INDEX idx_silver_customers_country ON silver.silver_customers(country);
END
GO

-- Silver Products Table
-- Cleaned and enriched product data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'silver_products' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.silver_products (
        product_id BIGINT PRIMARY KEY,
        product_name NVARCHAR(500),
        product_description NVARCHAR(MAX),
        
        -- Pricing
        regular_price FLOAT,
        sale_price FLOAT,
        cost_price FLOAT,
        profit_margin FLOAT,
        discount_percentage FLOAT,
        
        -- Inventory
        sku VARCHAR(100),
        quantity_available INT,
        is_unlimited BIT,
        
        -- Classification
        product_type VARCHAR(50),
        product_status VARCHAR(50),
        is_active BIT,
        
        -- Physical attributes
        weight FLOAT,
        weight_unit VARCHAR(20),
        
        -- Flags
        with_tax BIT,
        is_taxable BIT,
        requires_shipping BIT,
        
        -- SEO
        meta_title NVARCHAR(500),
        meta_description NVARCHAR(1000),
        
        -- Audit fields
        created_at DATETIME2,
        updated_at DATETIME2,
        processed_at DATETIME2 DEFAULT GETDATE()
    );
    
    -- Create indexes
    CREATE INDEX idx_silver_products_sku ON silver.silver_products(sku);
    CREATE INDEX idx_silver_products_status ON silver.silver_products(product_status);
    CREATE INDEX idx_silver_products_active ON silver.silver_products(is_active);
END
GO

PRINT 'Silver layer tables created successfully';
