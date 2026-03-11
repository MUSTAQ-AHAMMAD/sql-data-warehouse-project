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
IF OBJECT_ID('silver.silver_odoo_order_lines', 'U') IS NOT NULL DROP TABLE silver.silver_odoo_order_lines;
IF OBJECT_ID('silver.silver_odoo_orders', 'U') IS NOT NULL DROP TABLE silver.silver_odoo_orders;
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

-- ============================================
-- Odoo ERP Silver Tables
-- ============================================

-- Create Silver Odoo Orders Table (cleansed and typed)
CREATE TABLE silver.silver_odoo_orders (
    order_id                INT             NOT NULL,
    order_name              NVARCHAR(50)    NOT NULL,
    order_date              DATE            NULL,
    order_state             NVARCHAR(50)    NULL,
    company                 NVARCHAR(255)   NULL,
    customer_id             INT             NULL,
    customer_name           NVARCHAR(255)   NULL,
    amount_untaxed          DECIMAL(15, 2)  NULL,
    amount_tax              DECIMAL(15, 2)  NULL,
    amount_total            DECIMAL(15, 2)  NULL,
    payment_method          NVARCHAR(100)   NULL,
    payment_slug            NVARCHAR(100)   NULL,
    is_cod                  BIT             NULL,
    shipping_city           NVARCHAR(100)   NULL,
    shipping_address        NVARCHAR(500)   NULL,
    shipment_id             NVARCHAR(50)    NULL,
    shipping_number         NVARCHAR(100)   NULL,
    tracking_number         NVARCHAR(100)   NULL,
    tracking_link           NVARCHAR(500)   NULL,
    salla_order_id          NVARCHAR(50)    NULL,
    salla_order_status      NVARCHAR(100)   NULL,
    salla_ref_id            NVARCHAR(50)    NULL,
    salla_store_instance_id INT             NULL,
    source_system           NVARCHAR(50)    DEFAULT 'odoo',
    processed_at            DATETIME2       DEFAULT GETDATE(),
    created_at              DATETIME2       DEFAULT GETDATE(),
    CONSTRAINT pk_silver_odoo_orders PRIMARY KEY (order_id)
);
GO

-- Create Silver Odoo Order Lines Table (cleansed and typed)
CREATE TABLE silver.silver_odoo_order_lines (
    order_line_id       INT             NOT NULL,
    order_id            INT             NOT NULL,
    product_description NVARCHAR(500)   NULL,
    product_name        NVARCHAR(500)   NULL,
    product_barcode     NVARCHAR(100)   NULL,
    price_unit          DECIMAL(15, 2)  NULL,
    price_without_tax   DECIMAL(15, 2)  NULL,
    price_with_tax      DECIMAL(15, 2)  NULL,
    quantity            DECIMAL(15, 4)  NULL,
    salla_line_id       NVARCHAR(50)    NULL,
    source_system       NVARCHAR(50)    DEFAULT 'odoo',
    processed_at        DATETIME2       DEFAULT GETDATE(),
    created_at          DATETIME2       DEFAULT GETDATE(),
    CONSTRAINT pk_silver_odoo_order_lines PRIMARY KEY (order_line_id),
    CONSTRAINT fk_silver_odoo_lines_order
        FOREIGN KEY (order_id) REFERENCES silver.silver_odoo_orders(order_id)
);
GO

-- Indexes for Odoo silver tables
CREATE INDEX idx_silver_odoo_orders_date        ON silver.silver_odoo_orders(order_date);
CREATE INDEX idx_silver_odoo_orders_state       ON silver.silver_odoo_orders(order_state);
CREATE INDEX idx_silver_odoo_orders_customer    ON silver.silver_odoo_orders(customer_id);
CREATE INDEX idx_silver_odoo_lines_order        ON silver.silver_odoo_order_lines(order_id);
CREATE INDEX idx_silver_odoo_lines_barcode      ON silver.silver_odoo_order_lines(product_barcode);
GO

PRINT '✅ Silver layer tables created successfully';
GO
