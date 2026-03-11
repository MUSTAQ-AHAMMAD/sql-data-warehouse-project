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
IF OBJECT_ID('bronze.bronze_odoo_order_lines', 'U') IS NOT NULL DROP TABLE bronze.bronze_odoo_order_lines;
IF OBJECT_ID('bronze.bronze_odoo_orders', 'U') IS NOT NULL DROP TABLE bronze.bronze_odoo_orders;
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

-- ============================================
-- Odoo ERP Bronze Tables
-- ============================================

-- Create Bronze Odoo Orders Table
CREATE TABLE bronze.bronze_odoo_orders (
    order_id                            INT             NOT NULL,
    date_order                          DATETIME2       NULL,
    company                             NVARCHAR(255)   NULL,
    order_state                         NVARCHAR(50)    NULL,
    order_name                          NVARCHAR(50)    NOT NULL,
    customer_id                         INT             NULL,
    customer_name                       NVARCHAR(255)   NULL,
    order_amount_untaxed                DECIMAL(15, 2)  NULL,
    order_amount_tax                    DECIMAL(15, 2)  NULL,
    order_amount_total                  DECIMAL(15, 2)  NULL,
    ibq_salla_order                     BIT             NULL,
    ibq_salla_order_complete            NVARCHAR(100)   NULL,
    ibq_salla_order_courier_name        NVARCHAR(100)   NULL,
    ibq_salla_order_date                DATETIME2       NULL,
    ibq_salla_order_id                  NVARCHAR(50)    NULL,
    ibq_salla_order_operation           NVARCHAR(50)    NULL,
    ibq_salla_order_payment_methods_id  INT             NULL,
    ibq_is_cod                          BIT             NULL,
    ibq_salla_order_payment_name        NVARCHAR(100)   NULL,
    ibq_salla_order_payment_slug        NVARCHAR(100)   NULL,
    ibq_salla_order_ref_id              NVARCHAR(50)    NULL,
    ibq_salla_order_ship_to             NVARCHAR(500)   NULL,
    ibq_salla_order_ship_to_city        NVARCHAR(100)   NULL,
    ibq_salla_order_shipment_id         NVARCHAR(50)    NULL,
    ibq_salla_order_shipping_number     NVARCHAR(100)   NULL,
    ibq_salla_order_shipping_pdf        NVARCHAR(500)   NULL,
    ibq_salla_order_status_id           INT             NULL,
    ibq_salla_order_status_name         NVARCHAR(100)   NULL,
    ibq_salla_order_tracking_link       NVARCHAR(500)   NULL,
    ibq_salla_order_tracking_number     NVARCHAR(100)   NULL,
    ibq_salla_order_update_date         DATETIME2       NULL,
    ibq_salla_store_instance_id         INT             NULL,
    raw_data                            NVARCHAR(MAX)   NULL,
    source_system                       NVARCHAR(50)    DEFAULT 'odoo',
    extracted_at                        DATETIME2       DEFAULT GETDATE(),
    created_at                          DATETIME2       DEFAULT GETDATE(),
    CONSTRAINT pk_bronze_odoo_orders PRIMARY KEY (order_id)
);
GO

-- Create Bronze Odoo Order Lines Table
CREATE TABLE bronze.bronze_odoo_order_lines (
    order_line_id               INT             NOT NULL,
    order_id                    INT             NOT NULL,
    name                        NVARCHAR(500)   NULL,
    product_name                NVARCHAR(500)   NULL,
    product_barcode             NVARCHAR(100)   NULL,
    price_without_tax           DECIMAL(15, 2)  NULL,
    price_with_tax              DECIMAL(15, 2)  NULL,
    price_unit                  DECIMAL(15, 2)  NULL,
    qty                         DECIMAL(15, 4)  NULL,
    ibq_salla_order_line        BIT             NULL,
    ibq_salla_order_line_id     NVARCHAR(50)    NULL,
    raw_data                    NVARCHAR(MAX)   NULL,
    source_system               NVARCHAR(50)    DEFAULT 'odoo',
    extracted_at                DATETIME2       DEFAULT GETDATE(),
    created_at                  DATETIME2       DEFAULT GETDATE(),
    CONSTRAINT pk_bronze_odoo_order_lines PRIMARY KEY (order_line_id)
);
GO

-- Create indexes for Odoo tables
CREATE INDEX idx_bronze_odoo_orders_extracted   ON bronze.bronze_odoo_orders(extracted_at);
CREATE INDEX idx_bronze_odoo_orders_name        ON bronze.bronze_odoo_orders(order_name);
CREATE INDEX idx_bronze_odoo_orders_state       ON bronze.bronze_odoo_orders(order_state);
CREATE INDEX idx_bronze_odoo_lines_order        ON bronze.bronze_odoo_order_lines(order_id);
CREATE INDEX idx_bronze_odoo_lines_extracted    ON bronze.bronze_odoo_order_lines(extracted_at);
GO

PRINT '✅ Bronze layer tables created successfully';
GO
