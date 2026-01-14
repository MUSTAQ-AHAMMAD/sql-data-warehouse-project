# Migration Guide: Snowflake to SQL Server (On-Premise)

## Overview

This guide helps you migrate from cloud-based Snowflake to on-premise SQL Server while maintaining the same ETL pipeline architecture and functionality. This migration is ideal for organizations with confidential data that must remain on-premise.

## Table of Contents
1. [Why SQL Server On-Premise?](#why-sql-server-on-premise)
2. [Challenges and Solutions](#challenges-and-solutions)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Migration](#step-by-step-migration)
5. [Configuration Changes](#configuration-changes)
6. [Testing the Migration](#testing-the-migration)
7. [Performance Optimization](#performance-optimization)
8. [Future Extensibility](#future-extensibility)

---

## Why SQL Server On-Premise?

### Benefits
✅ **Data Security**: Keep confidential data within your network  
✅ **Compliance**: Meet regulatory requirements for data residency  
✅ **No Cloud Costs**: Avoid recurring cloud database costs  
✅ **Full Control**: Complete control over hardware, backups, and security  
✅ **Existing Infrastructure**: Leverage existing SQL Server licenses and expertise  

### Trade-offs
⚠️ **Manual Scaling**: You manage hardware and capacity  
⚠️ **Maintenance**: You're responsible for backups, updates, patches  
⚠️ **High Availability**: You need to configure clustering/replication  
⚠️ **Initial Setup**: More initial configuration required  

---

## Challenges and Solutions

### Challenge 1: JSON Data Handling
**Problem**: Snowflake VARIANT columns vs SQL Server NVARCHAR(MAX)

**Solution**:
- SQL Server 2016+ supports `JSON_VALUE()`, `JSON_QUERY()`, `OPENJSON()`
- Store JSON as NVARCHAR(MAX) in Bronze layer
- Extract to columns in Silver layer using JSON functions

```sql
-- Extract from JSON in SQL Server
SELECT 
    id,
    JSON_VALUE(shipping_address, '$.city') as shipping_city,
    JSON_VALUE(shipping_address, '$.country') as shipping_country
FROM bronze.bronze_orders;
```

### Challenge 2: Auto-scaling
**Problem**: Snowflake auto-scales; SQL Server doesn't

**Solution**:
- Size hardware appropriately for peak loads
- Implement table partitioning for large datasets
- Use indexed views for frequently accessed aggregations
- Schedule maintenance during off-peak hours

### Challenge 3: Connectivity from Airflow
**Problem**: Different connection libraries and authentication

**Solution**:
- Use `pyodbc` instead of `snowflake-connector-python`
- Support both Windows Authentication and SQL Authentication
- Configure SQL Server for remote connections
- Open firewall port 1433

### Challenge 4: Incremental Loading
**Problem**: Need efficient change data capture

**Solution**:
- Implement CDC (Change Data Capture) in SQL Server
- Use `MERGE` statements for upserts
- Track watermarks (last_loaded_timestamp)
- Implement proper indexing on timestamp columns

---

## Prerequisites

### SQL Server Requirements
- **Version**: SQL Server 2016 or later (for JSON support)
- **Edition**: Standard or Enterprise (Express has 10GB limit)
- **Memory**: Minimum 8GB RAM (16GB+ recommended)
- **Disk**: SSD recommended for data files
- **Network**: Port 1433 open for remote connections

### Windows Server Setup
```powershell
# Enable SQL Server remote connections
# Run in SQL Server Configuration Manager:
# 1. Enable TCP/IP protocol
# 2. Set TCP Port to 1433
# 3. Restart SQL Server service

# Open firewall port
New-NetFirewallRule -DisplayName "SQL Server" -Direction Inbound -LocalPort 1433 -Protocol TCP -Action Allow
```

### Python Environment
```bash
# Install SQL Server dependencies
pip install pyodbc==5.0.1
pip install pymssql==2.2.11
pip install sqlalchemy==2.0.25
pip install apache-airflow-providers-microsoft-mssql==3.6.0

# Remove Snowflake dependencies (optional)
pip uninstall snowflake-connector-python snowflake-sqlalchemy apache-airflow-providers-snowflake
```

### ODBC Driver Installation
**Windows**:
- Download and install [Microsoft ODBC Driver 17 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

**Linux (for Airflow server)**:
```bash
# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

---

## Step-by-Step Migration

### Step 1: Create SQL Server Database

```sql
-- Connect to SQL Server and create database
CREATE DATABASE SALLA_DWH;
GO

ALTER DATABASE SALLA_DWH SET RECOVERY SIMPLE; -- For development
-- ALTER DATABASE SALLA_DWH SET RECOVERY FULL; -- For production
GO
```

### Step 2: Run Schema Scripts

```bash
# Navigate to project directory
cd /path/to/sql-data-warehouse-project

# Run scripts in SQL Server Management Studio or via command line
sqlcmd -S localhost -d SALLA_DWH -i sql/sqlserver/bronze/create_bronze_tables.sql
sqlcmd -S localhost -d SALLA_DWH -i sql/sqlserver/silver/create_silver_tables.sql
sqlcmd -S localhost -d SALLA_DWH -i sql/sqlserver/gold/create_gold_tables.sql
```

### Step 3: Update Configuration

**Update `.env` file**:
```bash
# Comment out Snowflake configuration
# SNOWFLAKE_ACCOUNT=your_account
# SNOWFLAKE_USER=your_username
# SNOWFLAKE_PASSWORD=your_password
# SNOWFLAKE_WAREHOUSE=your_warehouse
# SNOWFLAKE_DATABASE=SALLA_DWH

# Add SQL Server configuration
SQLSERVER_HOST=localhost  # or IP address like 192.168.1.100
SQLSERVER_PORT=1433
SQLSERVER_DATABASE=SALLA_DWH
SQLSERVER_USER=your_sql_username  # Leave empty for Windows Auth
SQLSERVER_PASSWORD=your_sql_password  # Leave empty for Windows Auth
SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server
SQLSERVER_TRUSTED_CONNECTION=False  # Set to True for Windows Auth

# Keep existing Salla API configuration
SALLA_API_BASE_URL=https://api.salla.dev/admin/v2
SALLA_API_TOKEN=your_bearer_token
API_BATCH_SIZE=100
API_MAX_RETRIES=3
API_RETRY_DELAY=5
```

### Step 4: Update Python Code

**Option A: Minimal Changes** (Use adapter pattern)

Create `src/database/database_factory.py`:
```python
from src.database.snowflake_connector import SnowflakeConnector
from src.database.sqlserver_connector import SQLServerConnector
import os

def get_database_connector():
    """
    Factory method to get the appropriate database connector.
    Determines which database to use based on environment variable.
    """
    db_type = os.getenv('DATABASE_TYPE', 'sqlserver').lower()
    
    if db_type == 'snowflake':
        return SnowflakeConnector()
    elif db_type == 'sqlserver':
        return SQLServerConnector()
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
```

**Update transformation scripts**:
```python
# In bronze_extractor.py, silver_transformer.py, gold_transformer.py
# Replace:
from src.database.snowflake_connector import SnowflakeConnector

# With:
from src.database.database_factory import get_database_connector

# Replace instances of:
self.snowflake = SnowflakeConnector()

# With:
self.database = get_database_connector()
```

### Step 5: Update Airflow Configuration

**Update `requirements.txt`**:
```txt
# Add SQL Server provider
apache-airflow-providers-microsoft-mssql==3.6.0

# Add pyodbc
pyodbc==5.0.1
```

**Configure Airflow Connection**:
```bash
# Via CLI
airflow connections add 'sqlserver_default' \
    --conn-type 'mssql' \
    --conn-host 'localhost' \
    --conn-schema 'SALLA_DWH' \
    --conn-login 'your_username' \
    --conn-password 'your_password' \
    --conn-port 1433

# Or via Airflow UI:
# Admin → Connections → Add Connection
# Connection Id: sqlserver_default
# Connection Type: Microsoft SQL Server
# Host: localhost
# Schema: SALLA_DWH
# Login: your_username
# Password: your_password
# Port: 1433
```

### Step 6: Test Connection

```python
# Test script: test_sqlserver_connection.py
from src.database.sqlserver_connector import SQLServerConnector

try:
    with SQLServerConnector() as sql:
        result = sql.execute_query("SELECT @@VERSION as version")
        print(f"✓ Connected successfully!")
        print(f"SQL Server version: {result[0]['version']}")
        
        # Test schema exists
        schemas = sql.execute_query("""
            SELECT name FROM sys.schemas 
            WHERE name IN ('bronze', 'silver', 'gold')
        """)
        print(f"✓ Found {len(schemas)} schemas: {[s['name'] for s in schemas]}")
        
except Exception as e:
    print(f"✗ Connection failed: {str(e)}")
```

---

## Configuration Changes

### Update .env File

```bash
# Database selection
DATABASE_TYPE=sqlserver  # or 'snowflake' to switch back

# SQL Server Configuration (On-Premise)
SQLSERVER_HOST=192.168.1.100  # Your Windows laptop IP
SQLSERVER_PORT=1433
SQLSERVER_DATABASE=SALLA_DWH
SQLSERVER_USER=etl_user  # Create dedicated user
SQLSERVER_PASSWORD=strong_password_here
SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server
SQLSERVER_TRUSTED_CONNECTION=False

# For Windows Authentication (if Airflow runs on same Windows machine)
# SQLSERVER_TRUSTED_CONNECTION=True
# SQLSERVER_USER=
# SQLSERVER_PASSWORD=
```

### Create Dedicated SQL Server User

```sql
-- Create login and user for ETL process
USE master;
GO

CREATE LOGIN etl_user WITH PASSWORD = 'strong_password_here';
GO

USE SALLA_DWH;
GO

CREATE USER etl_user FOR LOGIN etl_user;
GO

-- Grant necessary permissions
ALTER ROLE db_datareader ADD MEMBER etl_user;
ALTER ROLE db_datawriter ADD MEMBER etl_user;
ALTER ROLE db_ddladmin ADD MEMBER etl_user;  -- For schema changes
GO

-- Grant execute permissions on schemas
GRANT EXECUTE ON SCHEMA::bronze TO etl_user;
GRANT EXECUTE ON SCHEMA::silver TO etl_user;
GRANT EXECUTE ON SCHEMA::gold TO etl_user;
GO
```

---

## Testing the Migration

### 1. Test Data Loading

```python
# test_data_loading.py
from src.transformations.bronze_extractor import BronzeExtractor
from src.database.database_factory import get_database_connector
import os

os.environ['DATABASE_TYPE'] = 'sqlserver'

# Test bronze extraction
extractor = BronzeExtractor()
count = extractor.extract_orders(max_pages=1)
print(f"✓ Loaded {count} orders to SQL Server Bronze layer")

# Verify in database
with get_database_connector() as db:
    result = db.execute_query("SELECT COUNT(*) as cnt FROM bronze.bronze_orders")
    print(f"✓ Verified: {result[0]['cnt']} orders in database")
```

### 2. Test Transformations

```bash
# Run each transformation
python src/transformations/bronze_extractor.py
python src/transformations/silver_transformer.py
python src/transformations/gold_transformer.py
```

### 3. Test Airflow DAGs

```bash
# Test DAG parsing
airflow dags list | grep salla

# Test single DAG
airflow dags test salla_bronze_extraction 2026-01-14
```

### 4. Verify Data Quality

```sql
-- Check record counts by layer
SELECT 'Bronze Orders' as layer, COUNT(*) as count FROM bronze.bronze_orders
UNION ALL
SELECT 'Silver Orders', COUNT(*) FROM silver.silver_orders
UNION ALL
SELECT 'Gold Fact Orders', COUNT(*) FROM gold.gold_fact_orders;

-- Check data freshness
SELECT 
    MAX(loaded_at) as latest_bronze_load,
    MAX(processed_at) as latest_silver_process
FROM bronze.bronze_orders
CROSS APPLY (SELECT MAX(processed_at) as processed_at FROM silver.silver_orders) s;
```

---

## Performance Optimization

### 1. Indexing Strategy

```sql
-- Add columnstore indexes for analytics (SQL Server 2016+)
CREATE NONCLUSTERED COLUMNSTORE INDEX ncix_fact_orders_analytics
ON gold.gold_fact_orders (order_date_key, customer_key, total_amount);

-- Add filtered indexes for common queries
CREATE INDEX idx_orders_recent 
ON silver.silver_orders (order_date, customer_id)
WHERE order_date >= DATEADD(month, -6, GETDATE());
```

### 2. Table Partitioning

```sql
-- Partition by date for large fact tables
CREATE PARTITION FUNCTION pf_OrderDate (DATETIME2)
AS RANGE RIGHT FOR VALUES (
    '2024-01-01', '2024-02-01', '2024-03-01', 
    '2024-04-01', '2024-05-01', '2024-06-01'
);

CREATE PARTITION SCHEME ps_OrderDate
AS PARTITION pf_OrderDate
ALL TO ([PRIMARY]);

-- Apply to table (for new tables)
CREATE TABLE gold.gold_fact_orders_partitioned (
    ...
) ON ps_OrderDate(order_date_key);
```

### 3. Enable Change Data Capture (CDC)

```sql
-- Enable CDC on database
USE SALLA_DWH;
GO

EXEC sys.sp_cdc_enable_db;
GO

-- Enable CDC on specific tables
EXEC sys.sp_cdc_enable_table
    @source_schema = N'bronze',
    @source_name = N'bronze_orders',
    @role_name = NULL;
GO
```

### 4. Implement Incremental Loading

```sql
-- Add watermark table
CREATE TABLE dbo.etl_watermarks (
    table_name VARCHAR(100) PRIMARY KEY,
    last_loaded_timestamp DATETIME2,
    last_loaded_id BIGINT,
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Use in queries
DECLARE @last_timestamp DATETIME2;
SELECT @last_timestamp = last_loaded_timestamp 
FROM dbo.etl_watermarks 
WHERE table_name = 'bronze_orders';

-- Load only new records
SELECT * FROM bronze.bronze_orders
WHERE loaded_at > @last_timestamp;

-- Update watermark after successful load
UPDATE dbo.etl_watermarks
SET last_loaded_timestamp = GETDATE(),
    updated_at = GETDATE()
WHERE table_name = 'bronze_orders';
```

---

## Future Extensibility

### Design for Multiple Data Sources

The architecture already supports extensibility. Here's how to add new data sources:

#### 1. Create Source-Specific Connector

```python
# src/api/new_source_connector.py
class NewSourceConnector:
    """Connector for new data source"""
    
    def fetch_data(self, endpoint: str) -> List[Dict]:
        # Implement data fetching logic
        pass
```

#### 2. Add Source-Specific Tables

```sql
-- Bronze layer for new source
CREATE TABLE bronze.bronze_newsource_entity (
    id BIGINT PRIMARY KEY,
    -- source-specific fields
    loaded_at DATETIME2 DEFAULT GETDATE(),
    source_system VARCHAR(50) DEFAULT 'NEW_SOURCE'
);
```

#### 3. Create Unified Transformation

```python
# src/transformations/unified_transformer.py
class UnifiedTransformer:
    """
    Transform data from multiple sources into unified format.
    """
    
    def transform_from_salla(self, data):
        # Salla-specific transformation
        pass
    
    def transform_from_new_source(self, data):
        # New source transformation
        pass
    
    def unify_to_silver(self):
        # Combine all sources into silver layer
        pass
```

#### 4. Update DAGs for New Sources

```python
# dags/unified_etl_dag.py
with DAG('unified_etl', ...) as dag:
    # Extract from multiple sources
    extract_salla = PythonOperator(task_id='extract_salla', ...)
    extract_new_source = PythonOperator(task_id='extract_new_source', ...)
    
    # Transform and combine
    transform = PythonOperator(task_id='transform_unified', ...)
    
    # Dependencies
    [extract_salla, extract_new_source] >> transform
```

### Best Practices for Scalability

1. **Source Isolation**: Keep each source in separate Bronze tables
2. **Schema Standardization**: Unify schemas in Silver layer
3. **Configurable Connectors**: Use factory pattern for different sources
4. **Metadata-Driven**: Store source configurations in database
5. **Monitoring**: Track load times and data quality per source

---

## Troubleshooting

### Common Issues

1. **Cannot connect to SQL Server from Airflow**
   - Check firewall rules
   - Verify SQL Server accepts remote connections
   - Test with `telnet <server> 1433`

2. **Windows Authentication not working**
   - Airflow must run under Windows account with database access
   - Or use SQL authentication instead

3. **Slow data loading**
   - Use bulk insert mode (`method='multi'` in pandas)
   - Disable indexes during bulk load, rebuild after
   - Consider using `BULK INSERT` or `bcp` utility

4. **JSON parsing errors**
   - Validate JSON before storing
   - Handle NULL values in JSON functions
   - Use TRY_CAST for safe conversions

---

## Comparison: Snowflake vs SQL Server

| Feature | Snowflake | SQL Server On-Premise |
|---------|-----------|----------------------|
| JSON Support | Native VARIANT | NVARCHAR(MAX) + functions |
| Auto-Scaling | ✅ Yes | ❌ Manual |
| Setup Complexity | Low | Medium |
| Data Security | Cloud | On-Premise ✅ |
| Cost Model | Pay-per-use | License + Hardware |
| Maintenance | Managed | Self-managed |
| Performance | Excellent | Good (with tuning) |
| HA/DR | Built-in | Manual setup |

---

## Next Steps

1. ✅ Complete migration steps above
2. ✅ Test with sample data
3. ✅ Monitor performance for 1 week
4. ✅ Setup backup and recovery procedures
5. ✅ Document any customizations
6. ✅ Train team on new setup
7. ✅ Plan for future data sources

For questions or issues, refer to:
- SQL Server documentation: https://docs.microsoft.com/sql
- Airflow SQL Server provider: https://airflow.apache.org/docs/apache-airflow-providers-microsoft-mssql
