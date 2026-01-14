-- Bronze Layer Schema: Raw data from Salla API
-- This layer stores data as close to the source as possible

-- Create database and schema if not exists
CREATE DATABASE IF NOT EXISTS SALLA_DWH;
USE DATABASE SALLA_DWH;
CREATE SCHEMA IF NOT EXISTS BRONZE;
USE SCHEMA BRONZE;

-- Bronze Orders Table
-- Stores raw order data from Salla API
CREATE TABLE IF NOT EXISTS bronze_orders (
    id NUMBER PRIMARY KEY,
    reference_id VARCHAR(100),
    status VARCHAR(50),
    amount FLOAT,
    currency VARCHAR(10),
    customer_id NUMBER,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    customer_mobile VARCHAR(50),
    payment_method VARCHAR(100),
    shipping_method VARCHAR(100),
    shipping_address VARIANT,
    items VARIANT,
    created_at TIMESTAMP_NTZ,
    updated_at TIMESTAMP_NTZ,
    notes VARCHAR(1000),
    coupon_code VARCHAR(100),
    discount_amount FLOAT,
    tax_amount FLOAT,
    shipping_cost FLOAT,
    total_amount FLOAT,
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'SALLA_API'
);

-- Bronze Customers Table
-- Stores raw customer data from Salla API
CREATE TABLE IF NOT EXISTS bronze_customers (
    id NUMBER PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    mobile VARCHAR(50),
    mobile_code VARCHAR(10),
    country VARCHAR(100),
    city VARCHAR(100),
    gender VARCHAR(20),
    birthday DATE,
    avatar VARCHAR(500),
    addresses VARIANT,
    created_at TIMESTAMP_NTZ,
    updated_at TIMESTAMP_NTZ,
    status VARCHAR(50),
    notes VARCHAR(1000),
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'SALLA_API'
);

-- Bronze Products Table
-- Stores raw product data from Salla API
CREATE TABLE IF NOT EXISTS bronze_products (
    id NUMBER PRIMARY KEY,
    name VARCHAR(500),
    description VARCHAR(5000),
    price FLOAT,
    sale_price FLOAT,
    cost_price FLOAT,
    sku VARCHAR(100),
    quantity NUMBER,
    unlimited_quantity BOOLEAN,
    status VARCHAR(50),
    type VARCHAR(50),
    weight FLOAT,
    weight_unit VARCHAR(20),
    images VARIANT,
    categories VARIANT,
    options VARIANT,
    metadata_title VARCHAR(500),
    metadata_description VARCHAR(1000),
    created_at TIMESTAMP_NTZ,
    updated_at TIMESTAMP_NTZ,
    with_tax BOOLEAN,
    is_taxable BOOLEAN,
    require_shipping BOOLEAN,
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'SALLA_API'
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bronze_orders_customer ON bronze_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_bronze_orders_created ON bronze_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_bronze_orders_status ON bronze_orders(status);

CREATE INDEX IF NOT EXISTS idx_bronze_customers_email ON bronze_customers(email);
CREATE INDEX IF NOT EXISTS idx_bronze_customers_created ON bronze_customers(created_at);

CREATE INDEX IF NOT EXISTS idx_bronze_products_sku ON bronze_products(sku);
CREATE INDEX IF NOT EXISTS idx_bronze_products_status ON bronze_products(status);
CREATE INDEX IF NOT EXISTS idx_bronze_products_created ON bronze_products(created_at);
