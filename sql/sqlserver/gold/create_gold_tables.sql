-- Gold Layer Schema for SQL Server: Business-ready dimensional model
-- This layer contains dimension and fact tables optimized for analytics

USE SALLA_DWH;
GO

-- Create Gold schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'gold')
BEGIN
    EXEC('CREATE SCHEMA gold');
END
GO

-- Dimension: Customers (SCD Type 2)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gold_dim_customers' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.gold_dim_customers (
        customer_key BIGINT IDENTITY(1,1) PRIMARY KEY,
        customer_id BIGINT,
        full_name NVARCHAR(500),
        first_name NVARCHAR(255),
        last_name NVARCHAR(255),
        email NVARCHAR(255),
        mobile VARCHAR(50),
        country NVARCHAR(100),
        city NVARCHAR(100),
        gender VARCHAR(20),
        age_group VARCHAR(50),
        customer_status VARCHAR(50),
        
        -- SCD Type 2 fields
        effective_date DATETIME2,
        expiration_date DATETIME2,
        is_current BIT DEFAULT 1,
        
        -- Audit fields
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE()
    );
    
    CREATE INDEX idx_gold_customers_id ON gold.gold_dim_customers(customer_id);
    CREATE INDEX idx_gold_customers_current ON gold.gold_dim_customers(is_current);
END
GO

-- Dimension: Products (SCD Type 2)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gold_dim_products' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.gold_dim_products (
        product_key BIGINT IDENTITY(1,1) PRIMARY KEY,
        product_id BIGINT,
        product_name NVARCHAR(500),
        product_description NVARCHAR(MAX),
        sku VARCHAR(100),
        product_type VARCHAR(50),
        product_status VARCHAR(50),
        regular_price FLOAT,
        sale_price FLOAT,
        discount_percentage FLOAT,
        weight FLOAT,
        weight_unit VARCHAR(20),
        is_active BIT,
        is_taxable BIT,
        requires_shipping BIT,
        
        -- SCD Type 2 fields
        effective_date DATETIME2,
        expiration_date DATETIME2,
        is_current BIT DEFAULT 1,
        
        -- Audit fields
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE()
    );
    
    CREATE INDEX idx_gold_products_id ON gold.gold_dim_products(product_id);
    CREATE INDEX idx_gold_products_current ON gold.gold_dim_products(is_current);
    CREATE INDEX idx_gold_products_sku ON gold.gold_dim_products(sku);
END
GO

-- Dimension: Date
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gold_dim_date' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.gold_dim_date (
        date_key INT PRIMARY KEY,
        full_date DATE,
        day_of_week INT,
        day_name VARCHAR(20),
        day_of_month INT,
        day_of_year INT,
        week_of_year INT,
        month_number INT,
        month_name VARCHAR(20),
        quarter INT,
        year INT,
        is_weekend BIT,
        is_holiday BIT,
        fiscal_year INT,
        fiscal_quarter INT
    );
END
GO

-- Dimension: Payment Method
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gold_dim_payment_method' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.gold_dim_payment_method (
        payment_method_key INT IDENTITY(1,1) PRIMARY KEY,
        payment_method_name VARCHAR(100),
        payment_type VARCHAR(50),
        is_active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE()
    );
END
GO

-- Dimension: Shipping Method
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gold_dim_shipping_method' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.gold_dim_shipping_method (
        shipping_method_key INT IDENTITY(1,1) PRIMARY KEY,
        shipping_method_name VARCHAR(100),
        shipping_type VARCHAR(50),
        is_active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE()
    );
END
GO

-- Fact: Orders
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gold_fact_orders' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.gold_fact_orders (
        order_key BIGINT IDENTITY(1,1) PRIMARY KEY,
        order_id BIGINT,
        reference_id VARCHAR(100),
        
        -- Foreign keys to dimensions
        customer_key BIGINT,
        order_date_key INT,
        payment_method_key INT,
        shipping_method_key INT,
        
        -- Order details
        order_status VARCHAR(50),
        items_count INT,
        
        -- Financial measures
        subtotal_amount FLOAT,
        discount_amount FLOAT,
        tax_amount FLOAT,
        shipping_cost FLOAT,
        total_amount FLOAT,
        currency VARCHAR(10),
        
        -- Degenerate dimensions
        coupon_code VARCHAR(100),
        
        -- Location
        shipping_country NVARCHAR(100),
        shipping_city NVARCHAR(100),
        
        -- Audit fields
        order_created_at DATETIME2,
        order_updated_at DATETIME2,
        loaded_at DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_orders_customer FOREIGN KEY (customer_key) REFERENCES gold.gold_dim_customers(customer_key),
        CONSTRAINT FK_orders_date FOREIGN KEY (order_date_key) REFERENCES gold.gold_dim_date(date_key),
        CONSTRAINT FK_orders_payment FOREIGN KEY (payment_method_key) REFERENCES gold.gold_dim_payment_method(payment_method_key),
        CONSTRAINT FK_orders_shipping FOREIGN KEY (shipping_method_key) REFERENCES gold.gold_dim_shipping_method(shipping_method_key)
    );
    
    CREATE INDEX idx_gold_fact_orders_customer ON gold.gold_fact_orders(customer_key);
    CREATE INDEX idx_gold_fact_orders_date ON gold.gold_fact_orders(order_date_key);
    CREATE INDEX idx_gold_fact_orders_status ON gold.gold_fact_orders(order_status);
END
GO

-- Fact: Order Items
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gold_fact_order_items' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.gold_fact_order_items (
        order_item_key BIGINT IDENTITY(1,1) PRIMARY KEY,
        order_key BIGINT,
        product_key BIGINT,
        
        -- Item details
        quantity INT,
        unit_price FLOAT,
        discount_amount FLOAT,
        tax_amount FLOAT,
        total_amount FLOAT,
        
        -- Audit fields
        loaded_at DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_items_order FOREIGN KEY (order_key) REFERENCES gold.gold_fact_orders(order_key),
        CONSTRAINT FK_items_product FOREIGN KEY (product_key) REFERENCES gold.gold_dim_products(product_key)
    );
    
    CREATE INDEX idx_gold_fact_items_order ON gold.gold_fact_order_items(order_key);
    CREATE INDEX idx_gold_fact_items_product ON gold.gold_fact_order_items(product_key);
END
GO

PRINT 'Gold layer tables created successfully';
