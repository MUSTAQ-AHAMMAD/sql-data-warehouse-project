# Data Warehouse Best Practices Guide

## Overview

This guide provides best practices for building and maintaining a production-grade data warehouse that supports multiple data sources, ensures data quality, and delivers accurate insights for business intelligence.

---

## Table of Contents

1. [Architecture Best Practices](#architecture-best-practices)
2. [Data Modeling Best Practices](#data-modeling-best-practices)
3. [ETL Pipeline Best Practices](#etl-pipeline-best-practices)
4. [Incremental Loading Strategies](#incremental-loading-strategies)
5. [Data Quality Best Practices](#data-quality-best-practices)
6. [Performance Optimization](#performance-optimization)
7. [Security Best Practices](#security-best-practices)
8. [Multi-Source Integration](#multi-source-integration)
9. [Power BI Optimization](#power-bi-optimization)
10. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Architecture Best Practices

### 1. Medallion Architecture (Bronze-Silver-Gold)

✅ **DO**:
- **Bronze Layer**: Store raw data exactly as received from sources
- **Silver Layer**: Clean, validate, and standardize data
- **Gold Layer**: Create business-ready, aggregated dimensional models
- Keep layers logically and physically separate
- Document transformation logic for each layer

❌ **DON'T**:
- Mix raw and transformed data in same tables
- Skip layers (always go Bronze → Silver → Gold)
- Store sensitive PII in logs or intermediate tables

### 2. Schema Design

✅ **DO**:
```sql
-- Use appropriate data types
CREATE TABLE gold.gold_fact_orders (
    order_id BIGINT NOT NULL,  -- Use BIGINT for IDs
    amount DECIMAL(18,2),  -- Use DECIMAL for money (not FLOAT)
    order_date DATE,  -- Use DATE/DATETIME2 appropriately
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Add constraints
ALTER TABLE gold.gold_fact_orders 
ADD CONSTRAINT PK_orders PRIMARY KEY (order_id);

ALTER TABLE gold.gold_fact_orders
ADD CONSTRAINT FK_orders_customer 
FOREIGN KEY (customer_key) REFERENCES gold.gold_dim_customers(customer_key);
```

❌ **DON'T**:
- Use VARCHAR(MAX) for everything
- Skip foreign key constraints
- Use FLOAT for monetary values

### 3. Naming Conventions

✅ **DO**:
- Use clear, descriptive names: `customer_total_orders` not `cto`
- Prefix by layer: `bronze_orders`, `silver_orders`, `gold_fact_orders`
- Use snake_case consistently
- Include measure types: `total_amount`, `avg_price`, `count_orders`

❌ **DON'T**:
- Use abbreviations: `cust`, `ord`, `prod`
- Mix naming styles: `CustomerName` vs `customer_email`
- Use reserved keywords as column names

---

## Data Modeling Best Practices

### 1. Star Schema Design

✅ **DO**:
```sql
-- Fact table with foreign keys to dimensions
CREATE TABLE gold.gold_fact_orders (
    order_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_key BIGINT,  -- FK to dim_customers
    product_key BIGINT,   -- FK to dim_products
    date_key INT,         -- FK to dim_date
    
    -- Measures
    quantity INT,
    unit_price DECIMAL(18,2),
    total_amount DECIMAL(18,2),
    
    FOREIGN KEY (customer_key) REFERENCES gold.gold_dim_customers(customer_key),
    FOREIGN KEY (product_key) REFERENCES gold.gold_dim_products(product_key),
    FOREIGN KEY (date_key) REFERENCES gold.gold_dim_date(date_key)
);
```

### 2. Slowly Changing Dimensions (SCD)

✅ **DO** - Implement SCD Type 2 for tracking history:
```sql
CREATE TABLE gold.gold_dim_customers (
    customer_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_id BIGINT,  -- Business key
    customer_name NVARCHAR(255),
    email NVARCHAR(255),
    
    -- SCD Type 2 fields
    effective_date DATETIME2,
    expiration_date DATETIME2,
    is_current BIT DEFAULT 1,
    
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Query current records only
SELECT * FROM gold.gold_dim_customers WHERE is_current = 1;

-- Get customer state at specific date
SELECT * FROM gold.gold_dim_customers 
WHERE customer_id = 123
  AND effective_date <= '2024-01-15'
  AND expiration_date > '2024-01-15';
```

### 3. Date Dimension

✅ **DO** - Create comprehensive date dimension:
```sql
CREATE TABLE gold.gold_dim_date (
    date_key INT PRIMARY KEY,  -- Format: YYYYMMDD
    full_date DATE,
    day_name VARCHAR(20),
    month_name VARCHAR(20),
    quarter INT,
    year INT,
    is_weekend BIT,
    is_holiday BIT,
    fiscal_year INT,
    fiscal_quarter INT
);

-- Pre-populate for 10 years
-- This enables fast date-based queries
```

---

## ETL Pipeline Best Practices

### 1. Idempotency

✅ **DO** - Make ETL jobs re-runnable:
```python
def load_orders(date: str):
    """
    Load orders for specific date.
    Can be run multiple times safely.
    """
    # Delete existing data for this date
    delete_query = """
        DELETE FROM silver.silver_orders 
        WHERE DATE(order_date) = ?
    """
    execute_query(delete_query, (date,))
    
    # Load fresh data
    load_new_orders(date)
```

❌ **DON'T**:
- Assume job runs only once
- Append without checking for duplicates
- Fail silently on errors

### 2. Error Handling

✅ **DO**:
```python
import logging

logger = logging.getLogger(__name__)

def extract_orders():
    try:
        orders = api.fetch_orders()
        logger.info(f"Fetched {len(orders)} orders")
        return orders
    except APIRateLimitError as e:
        logger.warning(f"Rate limited, retrying after {e.retry_after}s")
        time.sleep(e.retry_after)
        return extract_orders()
    except Exception as e:
        logger.error(f"Failed to fetch orders: {str(e)}", exc_info=True)
        raise  # Re-raise for Airflow to catch
```

### 3. Transaction Management

✅ **DO**:
```python
def load_batch(records):
    """Load records in transaction."""
    conn = get_connection()
    try:
        conn.begin()  # Start transaction
        
        for batch in chunk_records(records, 1000):
            load_batch_to_db(batch)
        
        conn.commit()  # Commit if all succeed
        logger.info(f"Successfully loaded {len(records)} records")
        
    except Exception as e:
        conn.rollback()  # Rollback on error
        logger.error(f"Transaction failed, rolled back: {str(e)}")
        raise
    finally:
        conn.close()
```

---

## Incremental Loading Strategies

### 1. Watermark-Based Loading

✅ **DO** - Track last loaded timestamp:
```sql
-- Create watermark table
CREATE TABLE dbo.etl_watermarks (
    source_table VARCHAR(100) PRIMARY KEY,
    last_loaded_timestamp DATETIME2,
    last_loaded_id BIGINT,
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Get watermark
DECLARE @last_timestamp DATETIME2;
SELECT @last_timestamp = last_loaded_timestamp 
FROM dbo.etl_watermarks 
WHERE source_table = 'salla_orders';

-- Load only new records
SELECT * FROM source_orders 
WHERE updated_at > @last_timestamp
ORDER BY updated_at;

-- Update watermark
UPDATE dbo.etl_watermarks
SET last_loaded_timestamp = GETDATE(),
    updated_at = GETDATE()
WHERE source_table = 'salla_orders';
```

### 2. Change Data Capture (CDC)

✅ **DO** - Enable CDC for tracking changes:
```sql
-- Enable CDC on SQL Server
EXEC sys.sp_cdc_enable_db;

EXEC sys.sp_cdc_enable_table
    @source_schema = 'bronze',
    @source_name = 'bronze_orders',
    @role_name = NULL;

-- Query changes
SELECT * FROM cdc.bronze_orders_CT
WHERE __$operation IN (2, 4)  -- 2=Insert, 4=Update
AND __$start_lsn > @last_lsn;
```

### 3. Merge Strategy

✅ **DO** - Use MERGE for upserts:
```sql
MERGE gold.gold_dim_customers AS target
USING (
    SELECT customer_id, customer_name, email, city
    FROM silver.silver_customers
    WHERE processed_at > @last_run
) AS source
ON target.customer_id = source.customer_id 
   AND target.is_current = 1
WHEN MATCHED AND (
    target.customer_name <> source.customer_name OR
    target.email <> source.email
) THEN
    UPDATE SET 
        is_current = 0,
        expiration_date = GETDATE()
WHEN NOT MATCHED THEN
    INSERT (customer_id, customer_name, email, effective_date, is_current)
    VALUES (source.customer_id, source.customer_name, source.email, GETDATE(), 1);
```

---

## Data Quality Best Practices

### 1. Data Validation

✅ **DO** - Validate at each layer:
```python
def validate_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Validate order data quality."""
    
    # Check required fields
    required_fields = ['order_id', 'customer_id', 'total_amount', 'order_date']
    missing_fields = [f for f in required_fields if f not in df.columns]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Check for nulls
    null_counts = df[required_fields].isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found: {null_counts[null_counts > 0]}")
        df = df.dropna(subset=required_fields)
    
    # Check data types
    df['order_id'] = pd.to_numeric(df['order_id'], errors='coerce')
    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
    
    # Check for duplicates
    duplicates = df.duplicated(subset=['order_id']).sum()
    if duplicates > 0:
        logger.warning(f"Found {duplicates} duplicate orders")
        df = df.drop_duplicates(subset=['order_id'], keep='last')
    
    # Business rules validation
    df = df[df['total_amount'] >= 0]  # No negative amounts
    df = df[df['order_date'] <= pd.Timestamp.now()]  # No future dates
    
    logger.info(f"Validation complete: {len(df)} valid records")
    return df
```

### 2. Data Quality Metrics

✅ **DO** - Track quality metrics:
```sql
-- Create DQ metrics table
CREATE TABLE dbo.data_quality_metrics (
    metric_date DATE,
    table_name VARCHAR(100),
    metric_name VARCHAR(100),
    metric_value DECIMAL(18,2),
    threshold_value DECIMAL(18,2),
    status VARCHAR(20),  -- 'PASS', 'WARN', 'FAIL'
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Example: Check null percentage
INSERT INTO dbo.data_quality_metrics 
SELECT 
    CAST(GETDATE() AS DATE),
    'silver.silver_orders',
    'null_customer_pct',
    CAST(SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(18,2)),
    5.0,  -- Threshold: 5%
    CASE 
        WHEN CAST(SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(18,2)) > 5.0 
        THEN 'FAIL' 
        ELSE 'PASS' 
    END
FROM silver.silver_orders
WHERE order_date >= DATEADD(day, -1, GETDATE());
```

---

## Performance Optimization

### 1. Indexing Strategy

✅ **DO**:
```sql
-- Clustered index on primary key
CREATE CLUSTERED INDEX idx_orders_pk 
ON gold.gold_fact_orders (order_key);

-- Non-clustered indexes on foreign keys
CREATE INDEX idx_orders_customer 
ON gold.gold_fact_orders (customer_key);

CREATE INDEX idx_orders_date 
ON gold.gold_fact_orders (order_date_key);

-- Filtered index for recent data
CREATE INDEX idx_orders_recent 
ON gold.gold_fact_orders (order_date_key, total_amount)
WHERE order_date_key >= 20240101;

-- Columnstore index for analytics
CREATE NONCLUSTERED COLUMNSTORE INDEX ncix_orders_analytics
ON gold.gold_fact_orders (order_date_key, customer_key, total_amount);
```

### 2. Partitioning

✅ **DO** - Partition large tables:
```sql
-- Partition by date range
CREATE PARTITION FUNCTION pf_OrderDate (INT)
AS RANGE RIGHT FOR VALUES (
    20240101, 20240201, 20240301, 20240401, 
    20240501, 20240601, 20240701, 20240801, 
    20240901, 20241001, 20241101, 20241201
);

CREATE PARTITION SCHEME ps_OrderDate
AS PARTITION pf_OrderDate
ALL TO ([PRIMARY]);

-- Apply to table
CREATE TABLE gold.gold_fact_orders_partitioned (
    order_key BIGINT IDENTITY(1,1),
    order_date_key INT,
    -- other fields
) ON ps_OrderDate(order_date_key);
```

### 3. Query Optimization

✅ **DO**:
```sql
-- Use appropriate joins
SELECT 
    f.order_id,
    c.customer_name,
    d.full_date,
    f.total_amount
FROM gold.gold_fact_orders f
INNER JOIN gold.gold_dim_customers c ON f.customer_key = c.customer_key AND c.is_current = 1
INNER JOIN gold.gold_dim_date d ON f.order_date_key = d.date_key
WHERE d.year = 2024;

-- Use covering indexes
CREATE INDEX idx_orders_covering
ON gold.gold_fact_orders (customer_key, order_date_key)
INCLUDE (total_amount, order_status);
```

---

## Security Best Practices

### 1. Access Control

✅ **DO**:
```sql
-- Create role-based access
CREATE ROLE analysts;
CREATE ROLE etl_users;

-- Grant appropriate permissions
GRANT SELECT ON SCHEMA::gold TO analysts;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::bronze TO etl_users;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::silver TO etl_users;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::gold TO etl_users;

-- Add users to roles
ALTER ROLE analysts ADD MEMBER john_analyst;
ALTER ROLE etl_users ADD MEMBER airflow_service;
```

### 2. Data Encryption

✅ **DO**:
```sql
-- Enable Transparent Data Encryption (TDE)
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'strong_password';

CREATE CERTIFICATE TDE_Cert WITH SUBJECT = 'TDE Certificate';

CREATE DATABASE ENCRYPTION KEY
WITH ALGORITHM = AES_256
ENCRYPTION BY SERVER CERTIFICATE TDE_Cert;

ALTER DATABASE SALLA_DWH SET ENCRYPTION ON;
```

### 3. Auditing

✅ **DO**:
```sql
-- Enable auditing
CREATE SERVER AUDIT data_warehouse_audit
TO FILE (FILEPATH = 'C:\Audit\');

CREATE DATABASE AUDIT SPECIFICATION dwh_audit_spec
FOR SERVER AUDIT data_warehouse_audit
ADD (SELECT, INSERT, UPDATE, DELETE ON SCHEMA::gold BY public);

ALTER SERVER AUDIT data_warehouse_audit WITH (STATE = ON);
ALTER DATABASE AUDIT SPECIFICATION dwh_audit_spec WITH (STATE = ON);
```

---

## Multi-Source Integration

### 1. Source Isolation

✅ **DO**:
```sql
-- Keep sources separate in Bronze
CREATE TABLE bronze.bronze_salla_orders (...);
CREATE TABLE bronze.bronze_shopify_orders (...);
CREATE TABLE bronze.bronze_woocommerce_orders (...);

-- Unify in Silver
CREATE TABLE silver.silver_orders (
    order_id BIGINT,
    source_system VARCHAR(50),  -- Track origin
    -- unified fields
);
```

### 2. Schema Mapping

✅ **DO** - Create mapping tables:
```sql
CREATE TABLE dbo.schema_mappings (
    source_system VARCHAR(50),
    source_field VARCHAR(100),
    target_field VARCHAR(100),
    transformation_rule VARCHAR(500),
    is_active BIT DEFAULT 1
);

-- Example mappings
INSERT INTO dbo.schema_mappings VALUES
('SALLA', 'amount', 'total_amount', 'CAST(amount AS DECIMAL(18,2))', 1),
('SHOPIFY', 'total_price', 'total_amount', 'CAST(total_price AS DECIMAL(18,2))', 1);
```

---

## Power BI Optimization

### 1. Design for BI

✅ **DO**:
```sql
-- Create summary tables/views
CREATE VIEW gold.vw_daily_sales AS
SELECT 
    d.full_date,
    d.year,
    d.month_name,
    COUNT(DISTINCT f.order_id) as order_count,
    SUM(f.total_amount) as total_sales,
    AVG(f.total_amount) as avg_order_value
FROM gold.gold_fact_orders f
JOIN gold.gold_dim_date d ON f.order_date_key = d.date_key
GROUP BY d.full_date, d.year, d.month_name;

-- Add calculated columns
ALTER TABLE gold.gold_fact_orders
ADD profit_amount AS (total_amount - cost_amount);
```

### 2. Import vs DirectQuery

✅ **DO**:
- Use **Import** for small datasets (< 1GB) - faster queries
- Use **DirectQuery** for large datasets - always current data
- Use **Composite** model for best of both

---

## Monitoring and Maintenance

### 1. Pipeline Monitoring

✅ **DO**:
```sql
-- Track pipeline runs
CREATE TABLE dbo.pipeline_runs (
    run_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    pipeline_name VARCHAR(100),
    start_time DATETIME2,
    end_time DATETIME2,
    status VARCHAR(20),  -- 'SUCCESS', 'FAILED', 'RUNNING'
    records_processed INT,
    error_message NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE()
);
```

### 2. Regular Maintenance

✅ **DO**:
```sql
-- Update statistics
UPDATE STATISTICS gold.gold_fact_orders;

-- Rebuild indexes
ALTER INDEX ALL ON gold.gold_fact_orders REBUILD;

-- Check fragmentation
SELECT 
    object_name(ips.object_id) as table_name,
    i.name as index_name,
    ips.avg_fragmentation_in_percent
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 30;
```

---

## Summary Checklist

✅ **Architecture**:
- [ ] Bronze-Silver-Gold layers implemented
- [ ] Clear separation of concerns
- [ ] Documented transformation logic

✅ **Data Quality**:
- [ ] Validation at each layer
- [ ] Quality metrics tracked
- [ ] Error handling in place

✅ **Performance**:
- [ ] Appropriate indexes created
- [ ] Large tables partitioned
- [ ] Statistics updated regularly

✅ **Security**:
- [ ] Role-based access control
- [ ] Encryption enabled
- [ ] Audit logging configured

✅ **Scalability**:
- [ ] Incremental loading implemented
- [ ] Multi-source support
- [ ] Monitoring in place

---

**Remember**: These are guidelines, not rigid rules. Adapt based on your specific requirements, data volumes, and business needs.
