-- Gold Layer Schema: Business-ready dimensional model
-- This layer contains dimension and fact tables optimized for analytics

USE DATABASE SALLA_DWH;
CREATE SCHEMA IF NOT EXISTS GOLD;
USE SCHEMA GOLD;

-- Dimension: Customers
-- Type 2 Slowly Changing Dimension to track customer history
CREATE TABLE IF NOT EXISTS gold_dim_customers (
    customer_key NUMBER AUTOINCREMENT PRIMARY KEY,
    customer_id NUMBER,
    full_name VARCHAR(500),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    mobile VARCHAR(50),
    country VARCHAR(100),
    city VARCHAR(100),
    gender VARCHAR(20),
    age_group VARCHAR(50),
    customer_status VARCHAR(50),
    
    -- SCD Type 2 fields
    effective_date TIMESTAMP_NTZ,
    expiration_date TIMESTAMP_NTZ,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Dimension: Products
-- Type 2 Slowly Changing Dimension to track product changes
CREATE TABLE IF NOT EXISTS gold_dim_products (
    product_key NUMBER AUTOINCREMENT PRIMARY KEY,
    product_id NUMBER,
    product_name VARCHAR(500),
    product_description VARCHAR(5000),
    sku VARCHAR(100),
    product_type VARCHAR(50),
    product_status VARCHAR(50),
    
    -- Current pricing
    regular_price FLOAT,
    sale_price FLOAT,
    discount_percentage FLOAT,
    
    -- Physical attributes
    weight FLOAT,
    weight_unit VARCHAR(20),
    
    -- Flags
    is_active BOOLEAN,
    is_taxable BOOLEAN,
    requires_shipping BOOLEAN,
    
    -- SCD Type 2 fields
    effective_date TIMESTAMP_NTZ,
    expiration_date TIMESTAMP_NTZ,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Dimension: Date
-- Standard date dimension for time-based analysis
CREATE TABLE IF NOT EXISTS gold_dim_date (
    date_key NUMBER PRIMARY KEY,
    full_date DATE,
    day_of_week NUMBER,
    day_name VARCHAR(20),
    day_of_month NUMBER,
    day_of_year NUMBER,
    week_of_year NUMBER,
    month_number NUMBER,
    month_name VARCHAR(20),
    quarter NUMBER,
    year NUMBER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    fiscal_year NUMBER,
    fiscal_quarter NUMBER
);

-- Dimension: Payment Method
CREATE TABLE IF NOT EXISTS gold_dim_payment_method (
    payment_method_key NUMBER AUTOINCREMENT PRIMARY KEY,
    payment_method_name VARCHAR(100),
    payment_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Dimension: Shipping Method
CREATE TABLE IF NOT EXISTS gold_dim_shipping_method (
    shipping_method_key NUMBER AUTOINCREMENT PRIMARY KEY,
    shipping_method_name VARCHAR(100),
    shipping_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Fact: Orders
-- Main fact table for order transactions
CREATE TABLE IF NOT EXISTS gold_fact_orders (
    order_key NUMBER AUTOINCREMENT PRIMARY KEY,
    order_id NUMBER,
    reference_id VARCHAR(100),
    
    -- Foreign keys to dimensions
    customer_key NUMBER,
    order_date_key NUMBER,
    payment_method_key NUMBER,
    shipping_method_key NUMBER,
    
    -- Order details
    order_status VARCHAR(50),
    items_count NUMBER,
    
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
    shipping_country VARCHAR(100),
    shipping_city VARCHAR(100),
    
    -- Audit fields
    order_created_at TIMESTAMP_NTZ,
    order_updated_at TIMESTAMP_NTZ,
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Foreign key constraints
    FOREIGN KEY (customer_key) REFERENCES gold_dim_customers(customer_key),
    FOREIGN KEY (order_date_key) REFERENCES gold_dim_date(date_key),
    FOREIGN KEY (payment_method_key) REFERENCES gold_dim_payment_method(payment_method_key),
    FOREIGN KEY (shipping_method_key) REFERENCES gold_dim_shipping_method(shipping_method_key)
);

-- Fact: Order Items (grain: one row per product per order)
CREATE TABLE IF NOT EXISTS gold_fact_order_items (
    order_item_key NUMBER AUTOINCREMENT PRIMARY KEY,
    order_key NUMBER,
    product_key NUMBER,
    
    -- Item details
    quantity NUMBER,
    unit_price FLOAT,
    discount_amount FLOAT,
    tax_amount FLOAT,
    total_amount FLOAT,
    
    -- Audit fields
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Foreign key constraints
    FOREIGN KEY (order_key) REFERENCES gold_fact_orders(order_key),
    FOREIGN KEY (product_key) REFERENCES gold_dim_products(product_key)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_gold_customers_id ON gold_dim_customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_gold_customers_current ON gold_dim_customers(is_current);

CREATE INDEX IF NOT EXISTS idx_gold_products_id ON gold_dim_products(product_id);
CREATE INDEX IF NOT EXISTS idx_gold_products_current ON gold_dim_products(is_current);
CREATE INDEX IF NOT EXISTS idx_gold_products_sku ON gold_dim_products(sku);

CREATE INDEX IF NOT EXISTS idx_gold_fact_orders_customer ON gold_fact_orders(customer_key);
CREATE INDEX IF NOT EXISTS idx_gold_fact_orders_date ON gold_fact_orders(order_date_key);
CREATE INDEX IF NOT EXISTS idx_gold_fact_orders_status ON gold_fact_orders(order_status);

CREATE INDEX IF NOT EXISTS idx_gold_fact_items_order ON gold_fact_order_items(order_key);
CREATE INDEX IF NOT EXISTS idx_gold_fact_items_product ON gold_fact_order_items(product_key);
