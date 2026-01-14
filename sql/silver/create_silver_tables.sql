-- Silver Layer Schema: Cleaned and enriched data
-- This layer contains validated, deduplicated, and standardized data

USE DATABASE SALLA_DWH;
CREATE SCHEMA IF NOT EXISTS SILVER;
USE SCHEMA SILVER;

-- Silver Orders Table
-- Cleaned and enriched order data
CREATE TABLE IF NOT EXISTS silver_orders (
    order_id NUMBER PRIMARY KEY,
    reference_id VARCHAR(100),
    order_status VARCHAR(50),
    order_date TIMESTAMP_NTZ,
    customer_id NUMBER,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    customer_mobile VARCHAR(50),
    payment_method VARCHAR(100),
    shipping_method VARCHAR(100),
    
    -- Address fields (extracted from VARIANT)
    shipping_country VARCHAR(100),
    shipping_city VARCHAR(100),
    shipping_address_line VARCHAR(500),
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
    notes VARCHAR(1000),
    items_count NUMBER,
    
    -- Audit fields
    created_at TIMESTAMP_NTZ,
    updated_at TIMESTAMP_NTZ,
    processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Silver Customers Table
-- Cleaned and enriched customer data
CREATE TABLE IF NOT EXISTS silver_customers (
    customer_id NUMBER PRIMARY KEY,
    full_name VARCHAR(500),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    mobile VARCHAR(50),
    mobile_code VARCHAR(10),
    
    -- Location fields
    country VARCHAR(100),
    city VARCHAR(100),
    
    -- Demographics
    gender VARCHAR(20),
    birthday DATE,
    age_group VARCHAR(50),
    
    -- Status
    customer_status VARCHAR(50),
    
    -- Metadata
    avatar_url VARCHAR(500),
    registration_date TIMESTAMP_NTZ,
    last_updated TIMESTAMP_NTZ,
    processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Silver Products Table
-- Cleaned and enriched product data
CREATE TABLE IF NOT EXISTS silver_products (
    product_id NUMBER PRIMARY KEY,
    product_name VARCHAR(500),
    product_description VARCHAR(5000),
    
    -- Pricing
    regular_price FLOAT,
    sale_price FLOAT,
    cost_price FLOAT,
    profit_margin FLOAT,
    discount_percentage FLOAT,
    
    -- Inventory
    sku VARCHAR(100),
    quantity_available NUMBER,
    is_unlimited BOOLEAN,
    
    -- Classification
    product_type VARCHAR(50),
    product_status VARCHAR(50),
    is_active BOOLEAN,
    
    -- Physical attributes
    weight FLOAT,
    weight_unit VARCHAR(20),
    
    -- Flags
    with_tax BOOLEAN,
    is_taxable BOOLEAN,
    requires_shipping BOOLEAN,
    
    -- SEO
    meta_title VARCHAR(500),
    meta_description VARCHAR(1000),
    
    -- Audit fields
    created_at TIMESTAMP_NTZ,
    updated_at TIMESTAMP_NTZ,
    processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_silver_orders_customer ON silver_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_silver_orders_date ON silver_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_silver_orders_status ON silver_orders(order_status);

CREATE INDEX IF NOT EXISTS idx_silver_customers_email ON silver_customers(email);
CREATE INDEX IF NOT EXISTS idx_silver_customers_country ON silver_customers(country);

CREATE INDEX IF NOT EXISTS idx_silver_products_sku ON silver_products(sku);
CREATE INDEX IF NOT EXISTS idx_silver_products_status ON silver_products(product_status);
CREATE INDEX IF NOT EXISTS idx_silver_products_active ON silver_products(is_active);
