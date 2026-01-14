# Maintenance and Operations Guide

This guide covers ongoing maintenance, monitoring, and troubleshooting for the Salla to Snowflake ETL pipeline.

## Daily Operations

### Monitoring Checklist

- [ ] Check Airflow UI for DAG run status
- [ ] Verify data freshness in Snowflake
- [ ] Review error logs if any failures
- [ ] Check Snowflake credit usage
- [ ] Validate data quality metrics

### Airflow Monitoring

#### Access Airflow UI

```bash
# Navigate to:
http://localhost:8080
```

#### Check DAG Status

1. View **DAGs** page for overall status
2. Click on DAG name to see:
   - Run history
   - Task duration
   - Success/failure rate
   - Recent logs

#### Review Task Logs

1. Click on DAG → Graph view
2. Click on specific task
3. Select **Log** to view detailed execution logs

### Snowflake Monitoring

#### Data Freshness Query

```sql
USE DATABASE SALLA_DWH;

-- Check latest load times
SELECT 
    'Bronze Orders' as layer,
    MAX(loaded_at) as last_load,
    COUNT(*) as record_count
FROM BRONZE.bronze_orders
UNION ALL
SELECT 
    'Silver Orders',
    MAX(processed_at),
    COUNT(*)
FROM SILVER.silver_orders
UNION ALL
SELECT 
    'Gold Fact Orders',
    MAX(loaded_at),
    COUNT(*)
FROM GOLD.gold_fact_orders;
```

#### Data Quality Checks

```sql
-- Check for null customer IDs in orders
SELECT COUNT(*) as null_customer_orders
FROM SILVER.silver_orders
WHERE customer_id IS NULL;

-- Check for duplicate orders
SELECT order_id, COUNT(*) as duplicate_count
FROM SILVER.silver_orders
GROUP BY order_id
HAVING COUNT(*) > 1;

-- Verify date dimension coverage
SELECT 
    MIN(full_date) as earliest_date,
    MAX(full_date) as latest_date,
    COUNT(*) as total_dates
FROM GOLD.gold_dim_date;
```

#### Credit Usage Monitoring

```sql
-- Check warehouse credit usage
SELECT 
    WAREHOUSE_NAME,
    SUM(CREDITS_USED) as total_credits,
    DATE_TRUNC('day', START_TIME) as day
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY WAREHOUSE_NAME, DATE_TRUNC('day', START_TIME)
ORDER BY day DESC;
```

## Weekly Maintenance

### Data Validation

Run weekly data validation script:

```python
# Create: src/utils/weekly_validation.py
from src.database.snowflake_connector import SnowflakeConnector

def validate_data_integrity():
    with SnowflakeConnector() as sf:
        # Check record counts match across layers
        bronze_count = sf.execute_query(
            "SELECT COUNT(*) as cnt FROM BRONZE.bronze_orders"
        )[0]['CNT']
        
        silver_count = sf.execute_query(
            "SELECT COUNT(*) as cnt FROM SILVER.silver_orders"
        )[0]['CNT']
        
        print(f"Bronze orders: {bronze_count}")
        print(f"Silver orders: {silver_count}")
        print(f"Match rate: {(silver_count/bronze_count)*100:.2f}%")

if __name__ == "__main__":
    validate_data_integrity()
```

### Performance Review

```sql
-- Identify slow queries
SELECT 
    QUERY_TEXT,
    EXECUTION_TIME,
    ROWS_PRODUCED,
    USER_NAME,
    START_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE EXECUTION_TIME > 10000  -- Queries taking > 10 seconds
AND START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY EXECUTION_TIME DESC
LIMIT 20;
```

### Log Cleanup

```bash
# Clean old Airflow logs (keep last 30 days)
airflow db clean --clean-before-timestamp $(date -d "30 days ago" +%Y-%m-%d)

# Clean old task logs
find $AIRFLOW_HOME/logs -name "*.log" -mtime +30 -delete
```

## Monthly Maintenance

### Database Optimization

#### Rebuild Clustered Tables

```sql
-- Reclustering for better query performance
ALTER TABLE GOLD.gold_fact_orders RECLUSTER;
ALTER TABLE GOLD.gold_dim_customers RECLUSTER;
ALTER TABLE GOLD.gold_dim_products RECLUSTER;
```

#### Update Statistics

```sql
-- Update table statistics
ANALYZE TABLE BRONZE.bronze_orders;
ANALYZE TABLE SILVER.silver_orders;
ANALYZE TABLE GOLD.gold_fact_orders;
```

#### Vacuum Old Data (if applicable)

```sql
-- Archive old bronze layer data (older than 90 days)
CREATE TABLE BRONZE.bronze_orders_archive AS
SELECT * FROM BRONZE.bronze_orders
WHERE loaded_at < DATEADD(day, -90, CURRENT_TIMESTAMP());

-- Delete archived data from main table
DELETE FROM BRONZE.bronze_orders
WHERE loaded_at < DATEADD(day, -90, CURRENT_TIMESTAMP());
```

### Dependency Updates

```bash
# Update Python packages
pip list --outdated

# Update specific packages
pip install --upgrade apache-airflow
pip install --upgrade snowflake-connector-python

# Update requirements.txt
pip freeze > requirements.txt
```

### Backup Verification

```sql
-- Test Time Travel functionality
SELECT * FROM BRONZE.bronze_orders
AT(OFFSET => -3600);  -- 1 hour ago

-- Test Fail-safe (within 7 days)
SELECT * FROM BRONZE.bronze_orders
BEFORE(TIMESTAMP => DATEADD(day, -1, CURRENT_TIMESTAMP()));
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. DAG Not Running

**Symptoms:**
- DAG shows as "paused"
- No scheduled runs appearing

**Solutions:**
```bash
# Check DAG is enabled
airflow dags unpause salla_bronze_extraction

# Manually trigger
airflow dags trigger salla_bronze_extraction

# Check scheduler is running
ps aux | grep "airflow scheduler"
```

#### 2. API Rate Limiting

**Symptoms:**
- 429 HTTP errors in logs
- Frequent retries

**Solutions:**
1. Reduce batch size in `.env`:
```bash
API_BATCH_SIZE=50
API_RETRY_DELAY=10
```

2. Add delay between requests in `salla_connector.py`

#### 3. Snowflake Connection Timeout

**Symptoms:**
- "Connection timeout" errors
- "Unable to connect" messages

**Solutions:**
```bash
# Check credentials
python -c "from src.database.snowflake_connector import SnowflakeConnector; \
           sf = SnowflakeConnector(); sf.connect(); print('Connected!')"

# Verify warehouse is running
# In Snowflake UI: Warehouses → Check status

# Check network connectivity
ping your_account.snowflakecomputing.com
```

#### 4. Out of Memory Errors

**Symptoms:**
- "MemoryError" in logs
- System slowdown during processing

**Solutions:**
1. Reduce batch size
2. Process data in smaller chunks
3. Increase system RAM
4. Use chunked DataFrame processing:

```python
# In transformation scripts
chunk_size = 1000
for chunk in pd.read_sql(query, connection, chunksize=chunk_size):
    process_chunk(chunk)
```

#### 5. Data Quality Issues

**Symptoms:**
- Null values in key fields
- Duplicate records
- Mismatched data types

**Solutions:**
```python
# Add validation in transformation scripts
def validate_orders(df):
    # Check for nulls in critical fields
    null_checks = df[['order_id', 'customer_id', 'total_amount']].isnull().sum()
    if null_checks.any():
        logger.warning(f"Null values found: {null_checks}")
    
    # Check for duplicates
    duplicates = df.duplicated(subset=['order_id']).sum()
    if duplicates > 0:
        logger.warning(f"Found {duplicates} duplicate orders")
        df = df.drop_duplicates(subset=['order_id'], keep='last')
    
    return df
```

#### 6. Airflow Webserver Crash

**Symptoms:**
- Cannot access Airflow UI
- "Connection refused" error

**Solutions:**
```bash
# Check if webserver is running
ps aux | grep "airflow webserver"

# Restart webserver
pkill -f "airflow webserver"
airflow webserver --port 8080 --daemon

# Check logs
tail -f $AIRFLOW_HOME/logs/webserver.log
```

### Log Locations

- **Airflow DAG logs**: `$AIRFLOW_HOME/logs/`
- **Airflow scheduler logs**: `$AIRFLOW_HOME/logs/scheduler/`
- **Task execution logs**: `$AIRFLOW_HOME/logs/dag_id/task_id/`
- **Snowflake query logs**: Available in Snowflake UI → History

## Performance Optimization

### Snowflake Optimization

```sql
-- Add clustering keys to frequently queried columns
ALTER TABLE GOLD.gold_fact_orders 
CLUSTER BY (order_date_key, customer_key);

-- Create materialized views for common queries
CREATE MATERIALIZED VIEW GOLD.mv_daily_sales AS
SELECT 
    d.full_date,
    SUM(f.total_amount) as daily_revenue,
    COUNT(DISTINCT f.order_id) as order_count
FROM GOLD.gold_fact_orders f
JOIN GOLD.gold_dim_date d ON f.order_date_key = d.date_key
GROUP BY d.full_date;
```

### Airflow Optimization

```python
# In DAG files, optimize task concurrency
default_args = {
    'max_active_runs': 1,  # One DAG run at a time
    'concurrency': 3,  # Max parallel tasks
}

# Use pools for resource management
# In Airflow UI: Admin → Pools
# Create pool: snowflake_pool with 5 slots
# In DAG:
task = PythonOperator(
    task_id='extract_orders',
    pool='snowflake_pool',
    ...
)
```

### API Optimization

```python
# Implement smart batching
def smart_batch_size():
    """Adjust batch size based on time of day"""
    from datetime import datetime
    hour = datetime.now().hour
    
    # Smaller batches during peak hours
    if 9 <= hour <= 17:
        return 50
    else:
        return 100
```

## Disaster Recovery

### Backup Strategy

1. **Snowflake Time Travel**: Automatic (90 days)
2. **Fail-Safe**: Automatic (7 days after Time Travel)
3. **Code Backup**: Git repository
4. **Configuration Backup**: Store `.env` securely (not in git)

### Recovery Procedures

#### Restore Data from Time Travel

```sql
-- Restore table to specific time
CREATE OR REPLACE TABLE BRONZE.bronze_orders AS
SELECT * FROM BRONZE.bronze_orders
AT(TIMESTAMP => '2024-01-15 10:00:00'::TIMESTAMP);

-- Restore deleted records
INSERT INTO BRONZE.bronze_orders
SELECT * FROM BRONZE.bronze_orders
BEFORE(STATEMENT => '<statement_id>');
```

#### Restore Airflow Metadata

```bash
# Backup Airflow DB
airflow db backup

# Restore from backup
airflow db restore airflow_backup.db
```

## Scaling Considerations

### When to Scale

Monitor these metrics:
- DAG execution time > 2 hours
- Task queue length > 10
- Snowflake credit usage > budget
- API rate limits frequently hit

### Scaling Options

1. **Horizontal Scaling**:
   - Add more Airflow workers
   - Partition data processing

2. **Vertical Scaling**:
   - Larger Snowflake warehouse
   - More memory for Airflow

3. **Optimization**:
   - Implement caching
   - Use incremental processing
   - Optimize SQL queries

## Support and Escalation

### Internal Escalation Path

1. **Level 1**: Check logs and error messages
2. **Level 2**: Review documentation and troubleshooting guide
3. **Level 3**: Contact Snowflake/Airflow support
4. **Level 4**: Engage development team

### External Resources

- Snowflake Support: support.snowflake.com
- Airflow Documentation: airflow.apache.org/docs
- Salla API Support: docs.salla.dev
- GitHub Issues: github.com/MUSTAQ-AHAMMAD/sql-data-warehouse-project

## Maintenance Schedule

| Task | Frequency | Day/Time |
|------|-----------|----------|
| Monitor DAG runs | Daily | Morning |
| Check data quality | Daily | After DAG completion |
| Review error logs | Daily | As needed |
| Validate data integrity | Weekly | Monday |
| Performance review | Weekly | Friday |
| Update dependencies | Monthly | First week |
| Database optimization | Monthly | Last weekend |
| Backup verification | Monthly | Mid-month |
| Disaster recovery test | Quarterly | Scheduled |

---

**Remember**: Proactive monitoring and maintenance prevent most issues. Keep logs clean, monitor performance, and stay current with updates.
