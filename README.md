# Salla API to Snowflake Data Warehouse - ETL Pipeline

## Overview

This project implements a scalable ETL (Extract, Transform, Load) pipeline that integrates Salla e-commerce APIs with Snowflake data warehouse using Apache Airflow for orchestration. The solution follows a three-tier data architecture (Bronze, Silver, Gold) optimized for batch processing and analytics.

## Architecture

### Data Layers

#### 1. Bronze Layer (Raw Data)
- **Purpose**: Store raw data exactly as received from Salla API
- **Tables**: 
  - `bronze_orders`: Raw order data
  - `bronze_customers`: Raw customer data
  - `bronze_products`: Raw product data
- **Characteristics**: 
  - Minimal transformation
  - VARIANT columns for complex JSON structures
  - Audit fields (loaded_at, source_system)

#### 2. Silver Layer (Cleaned Data)
- **Purpose**: Cleaned, validated, and enriched data
- **Tables**:
  - `silver_orders`: Cleaned order data with extracted fields
  - `silver_customers`: Deduplicated and standardized customer data
  - `silver_products`: Enriched product data with calculated metrics
- **Transformations**:
  - Data cleansing (nulls, duplicates removal)
  - Type conversions and standardization
  - JSON field extraction
  - Calculated fields (age groups, profit margins, etc.)

#### 3. Gold Layer (Business-Ready)
- **Purpose**: Dimensional model optimized for analytics and BI
- **Dimension Tables**:
  - `gold_dim_customers`: Customer dimension (SCD Type 2)
  - `gold_dim_products`: Product dimension (SCD Type 2)
  - `gold_dim_date`: Date dimension
  - `gold_dim_payment_method`: Payment methods
  - `gold_dim_shipping_method`: Shipping methods
- **Fact Tables**:
  - `gold_fact_orders`: Order transactions
  - `gold_fact_order_items`: Order line items
- **Characteristics**:
  - Star schema design
  - Optimized for Power BI queries
  - Foreign key relationships
  - Slowly Changing Dimensions (SCD Type 2)

### ETL Pipeline Flow

```
Salla API → Bronze Layer → Silver Layer → Gold Layer → Power BI
   ↓            ↓             ↓              ↓
Extract      Transform    Transform     Analytics
(Raw)        (Clean)     (Dimension)    (Visualize)
```

## Project Structure

```
sql-data-warehouse-project/
├── dags/
│   ├── salla_bronze_dag.py      # Airflow DAG for Bronze extraction
│   ├── salla_silver_dag.py      # Airflow DAG for Silver transformation
│   └── salla_gold_dag.py        # Airflow DAG for Gold dimensional model
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── salla_connector.py   # Salla API connector with retry logic
│   ├── database/
│   │   ├── __init__.py
│   │   └── snowflake_connector.py  # Snowflake database connector
│   ├── transformations/
│   │   ├── __init__.py
│   │   ├── bronze_extractor.py  # Bronze layer extraction
│   │   ├── silver_transformer.py # Silver layer transformation
│   │   └── gold_transformer.py  # Gold layer transformation
│   └── utils/
│       ├── __init__.py
│       └── setup_database.py    # Database schema setup script
├── sql/
│   ├── bronze/
│   │   └── create_bronze_tables.sql
│   ├── silver/
│   │   └── create_silver_tables.sql
│   └── gold/
│       └── create_gold_tables.sql
├── docs/
├── .env.example                 # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

## 📊 Performance Analysis and Documentation

### New: Data Fetch Performance Reports

Comprehensive performance analysis and documentation for Salla API data fetching:

- **📈 Performance Analyzer Tool** - Measure and analyze API fetch performance
  - Real-time performance measurement
  - Throughput analysis (records per second)
  - Memory profiling
  - Server impact assessment
  - Time estimation for full data extraction
  - Simulation mode for testing

- **📑 Technical Documentation**
  - [Data Fetch Performance Report](docs/DATA_FETCH_PERFORMANCE_REPORT.md) - Complete technical analysis
  - [Quick Reference Guide](docs/DATA_FETCH_QUICK_REFERENCE.md) - At-a-glance metrics and commands
  - [Salla Team Email Template](docs/SALLA_TEAM_EMAIL_TEMPLATE.md) - Ready-to-send notification
  - [Performance Tool Guide](tools/README.md) - Analyzer usage and integration

### Run Performance Analysis

```bash
# Quick analysis with simulation (no API calls)
python tools/performance_analyzer.py --sample

# Custom record estimates
python tools/performance_analyzer.py --sample --orders 10000 --customers 5000 --products 2000

# Live API testing (requires token)
python tools/performance_analyzer.py

# Export report to JSON
python tools/performance_analyzer.py --sample --output performance_report.json
```

### Key Performance Metrics

| Metric                    | Typical Value            | Status |
|---------------------------|--------------------------|--------|
| **Daily Load Time**       | 8-15 minutes             | ✅ Fast |
| **Initial Load Time**     | 1-2 hours (one-time)     | ✅ Acceptable |
| **Server Impact**         | LOW                      | ✅ Safe |
| **Request Rate**          | ~120 requests/minute     | ✅ Conservative |
| **Daily Data Transfer**   | 1-5 MB                   | ✅ Minimal |
| **Memory Usage**          | <500 MB peak             | ✅ Efficient |

> 📖 **See [Performance Report](docs/DATA_FETCH_PERFORMANCE_REPORT.md) for detailed analysis and [Quick Reference](docs/DATA_FETCH_QUICK_REFERENCE.md) for at-a-glance information**

## Features

### API Integration
- ✅ Bearer token authentication
- ✅ Batch processing (configurable batch size)
- ✅ Automatic pagination handling
- ✅ Rate limiting with exponential backoff
- ✅ Retry logic for failed requests
- ✅ Error handling and logging

### Data Processing
- ✅ Incremental loading (only new/updated records)
- ✅ Data validation and cleansing
- ✅ Type conversion and standardization
- ✅ JSON field extraction
- ✅ Calculated metrics (age groups, profit margins, discounts)
- ✅ Deduplication

### Airflow Orchestration
- ✅ Three separate DAGs for each layer
- ✅ Task dependencies and ordering
- ✅ External task sensors for layer synchronization
- ✅ Parallel task execution where possible
- ✅ Configurable retries and timeouts
- ✅ XCom for inter-task communication

### Dimensional Modeling
- ✅ Star schema design
- ✅ Slowly Changing Dimensions (Type 2)
- ✅ Date dimension with calendar attributes
- ✅ Lookup dimensions (payment, shipping methods)
- ✅ Fact tables with foreign key relationships

### 🆕 Enhanced Architecture (NEW!)
- ✅ **Generic API Adapter Interface** - Plugin-based architecture for multiple data sources
- ✅ **Data Source Registry** - Config-driven source management
- ✅ **Data Validation Framework** - Great Expectations integration
- ✅ **Error Handler with DLQ** - Dead Letter Queue for failed records
- ✅ **API Testing Dashboard** - Web UI for testing and monitoring
- ✅ **Real-time Quality Metrics** - Data profiling and validation
- ✅ **Schema Validation** - Automatic schema detection and validation
- ✅ **Error Tracking** - Centralized error logging and categorization

> 📖 **See [Enhanced Architecture Guide](docs/ENHANCED_ARCHITECTURE.md) for detailed documentation**

## Prerequisites

- Python 3.8 or higher
- Snowflake account with database credentials
- Salla API access token
- Apache Airflow 2.10.4 or higher
- Sufficient permissions to create databases and tables in Snowflake

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/MUSTAQ-AHAMMAD/sql-data-warehouse-project.git
cd sql-data-warehouse-project
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` file:

```bash
# Salla API Configuration
SALLA_API_BASE_URL=https://api.salla.dev/admin/v2
SALLA_API_TOKEN=your_actual_bearer_token

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=SALLA_DWH
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=your_role

# API Configuration (optional)
API_BATCH_SIZE=100
API_MAX_RETRIES=3
API_RETRY_DELAY=5
```

### 5. Set Up Database Schema

```bash
python src/utils/setup_database.py
```

This will create all necessary databases, schemas, and tables in Snowflake.

### 6. Configure Airflow

```bash
# Set Airflow home (optional)
export AIRFLOW_HOME=$(pwd)/airflow

# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Copy DAGs to Airflow DAGs folder
cp -r dags/* $AIRFLOW_HOME/dags/
```

### 7. Start Airflow

```bash
# Start Airflow webserver (in one terminal)
airflow webserver --port 8080

# Start Airflow scheduler (in another terminal)
airflow scheduler
```

Access Airflow UI at `http://localhost:8080`

## Usage

### Running the ETL Pipeline

#### Option 1: Through Airflow UI

1. Open Airflow UI at `http://localhost:8080`
2. Enable the DAGs:
   - `salla_bronze_extraction`
   - `salla_silver_transformation`
   - `salla_gold_dimensional`
3. Trigger the Bronze DAG first (others will follow automatically based on schedule)

#### Option 2: Command Line

```bash
# Trigger Bronze extraction
airflow dags trigger salla_bronze_extraction

# Wait for completion, then trigger Silver
airflow dags trigger salla_silver_transformation

# Wait for completion, then trigger Gold
airflow dags trigger salla_gold_dimensional
```

#### Option 3: Python Scripts (for testing)

```bash
# Extract to Bronze layer
python src/transformations/bronze_extractor.py

# Transform to Silver layer
python src/transformations/silver_transformer.py

# Transform to Gold layer
python src/transformations/gold_transformer.py
```

### DAG Schedules

- **Bronze Layer**: Daily at 2:00 AM UTC
- **Silver Layer**: Daily at 3:00 AM UTC (1 hour after Bronze)
- **Gold Layer**: Daily at 4:00 AM UTC (1 hour after Silver)

## Power BI Integration

### Connecting Power BI to Snowflake

1. Open Power BI Desktop
2. Click "Get Data" → "Snowflake"
3. Enter connection details:
   - Server: `your_account.region.snowflakecomputing.com`
   - Warehouse: `your_warehouse`
4. Select "Database" authentication
5. Navigate to: `SALLA_DWH` → `GOLD` schema
6. Select tables:
   - `gold_fact_orders`
   - `gold_dim_customers`
   - `gold_dim_products`
   - `gold_dim_date`
   - `gold_dim_payment_method`
   - `gold_dim_shipping_method`

### Sample Power BI Queries

The Gold layer is optimized for common analytics queries:

```sql
-- Sales by Customer
SELECT 
    c.full_name,
    COUNT(f.order_id) as total_orders,
    SUM(f.total_amount) as total_sales
FROM gold_fact_orders f
JOIN gold_dim_customers c ON f.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.full_name
ORDER BY total_sales DESC;

-- Sales by Date
SELECT 
    d.full_date,
    d.month_name,
    d.year,
    SUM(f.total_amount) as daily_sales
FROM gold_fact_orders f
JOIN gold_dim_date d ON f.order_date_key = d.date_key
GROUP BY d.full_date, d.month_name, d.year
ORDER BY d.full_date;

-- Top Products
SELECT 
    p.product_name,
    p.sku,
    COUNT(DISTINCT f.order_id) as order_count
FROM gold_fact_orders f
JOIN gold_dim_products p ON f.customer_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.product_name, p.sku
ORDER BY order_count DESC
LIMIT 10;
```

## Monitoring and Maintenance

### Airflow Monitoring

- Access Airflow UI to view DAG runs, task status, and logs
- Set up email alerts for failures (configure in DAG default_args)
- Review task duration and identify bottlenecks

### Snowflake Monitoring

```sql
-- Check record counts by layer
SELECT 'Bronze Orders' as layer, COUNT(*) FROM BRONZE.bronze_orders
UNION ALL
SELECT 'Silver Orders', COUNT(*) FROM SILVER.silver_orders
UNION ALL
SELECT 'Gold Fact Orders', COUNT(*) FROM GOLD.gold_fact_orders;

-- Check data freshness
SELECT 
    MAX(loaded_at) as latest_bronze_load,
    MAX(processed_at) as latest_silver_load
FROM BRONZE.bronze_orders, SILVER.silver_orders;
```

### Logs

All components use Python logging:
- API calls and responses
- Data transformation steps
- Error messages and stack traces
- Record counts and processing times

## Scaling Instructions

### Adding New API Endpoints

1. **Add API method** to `src/api/salla_connector.py`:
```python
def fetch_new_endpoint(self, page: int = 1, per_page: Optional[int] = None) -> Dict:
    per_page = per_page or self.batch_size
    params = {'page': page, 'per_page': per_page}
    return self._make_request('/new_endpoint', params)
```

2. **Create Bronze table** in `sql/bronze/`:
```sql
CREATE TABLE IF NOT EXISTS bronze_new_entity (
    -- Define schema based on API response
);
```

3. **Add extraction logic** to `src/transformations/bronze_extractor.py`

4. **Create Silver table and transformation logic**

5. **Update Gold layer** if needed for dimensional model

6. **Add tasks to Airflow DAGs**

### Horizontal Scaling

- Increase Airflow worker nodes for parallel processing
- Use Airflow pools to limit concurrent database connections
- Partition large tables in Snowflake
- Implement micro-batching for large datasets

### Performance Optimization

- Use Snowflake clustering keys for frequently queried columns
- Implement materialized views for common aggregations
- Enable Snowflake query result caching
- Optimize batch sizes based on API rate limits

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify Snowflake credentials in `.env`
   - Check network connectivity and firewall rules
   - Ensure Snowflake warehouse is running

2. **API Rate Limiting**
   - Reduce `API_BATCH_SIZE` in `.env`
   - Increase `API_RETRY_DELAY`
   - Implement longer delays between requests

3. **Airflow DAG Not Appearing**
   - Check DAG file for syntax errors
   - Verify AIRFLOW_HOME/dags directory
   - Refresh Airflow UI

4. **Data Quality Issues**
   - Review transformation logs
   - Check source data format
   - Validate data types and constraints

## 🚀 API Testing Dashboard

### Quick Start

Start the dashboard:
```bash
python start_dashboard.py --port 5000
```

Access the dashboard at: `http://localhost:5000`

### Dashboard Features

1. **API Testing**
   - Test all API endpoints
   - View real-time responses
   - Pagination support
   - Error handling

2. **Data Validation**
   - Schema validation
   - Quality checks
   - Data profiling
   - Type verification

3. **Quality Metrics**
   - Row/column counts
   - Null value analysis
   - Duplicate detection
   - Statistical summaries

4. **Error Tracking**
   - Error summary by severity
   - DLQ file management
   - Error categorization
   - Retry mechanisms

5. **Multi-Source Support**
   - Test multiple data sources
   - Connection validation
   - Config-driven setup
   - Real-time monitoring

### Configuration

Update `config/data_sources.yaml` to configure data sources:

```yaml
data_sources:
  salla:
    enabled: true
    api_token: ${SALLA_API_TOKEN}
    base_url: ${SALLA_API_BASE_URL}
    batch_size: 100
```

See [Enhanced Architecture Guide](docs/ENHANCED_ARCHITECTURE.md) for complete documentation.

## 🏥 Health Monitoring Dashboard

### Quick Start

Start the monitoring dashboard:
```bash
python start_monitoring.py --port 5001
```

Access the dashboard at: `http://localhost:5001`

### Dashboard Features

1. **Real-time Health Monitoring**
   - Auto-refreshes every 10 seconds
   - Overall system health status
   - Component-level status tracking

2. **Database Status**
   - Connection health
   - Database version information
   - Real-time connectivity checks

3. **API Status**
   - Salla API connectivity
   - Configuration validation
   - Token status

4. **Data Layers Metrics**
   - Bronze layer record counts (Orders, Customers, Products)
   - Silver layer record counts
   - Gold layer record counts (Dimensions and Facts)

5. **ETL Pipeline Tracking**
   - Last load timestamps
   - Records loaded per entity
   - Load duration and rate metrics
   - Watermark tracking

6. **REST API Endpoints**
   - `/api/health` - Get overall health status
   - `/api/stats` - Get detailed statistics

### Configuration

Configure using environment variables in `.env`:
```bash
MONITORING_HOST=0.0.0.0
MONITORING_PORT=5001
MONITORING_DEBUG=False
```

See [MONITORING_GUIDE.md](MONITORING_GUIDE.md) for complete documentation.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Check documentation in `/docs` folder
- Review Airflow logs for detailed error messages

## Acknowledgments

- Salla API documentation
- Apache Airflow community
- Snowflake documentation
- Power BI integration guides