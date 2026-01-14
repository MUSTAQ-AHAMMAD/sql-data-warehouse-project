# Architecture Documentation

## System Architecture Overview

The Salla to Snowflake ETL pipeline follows a modern data warehouse architecture with three distinct data layers (Bronze, Silver, Gold) orchestrated by Apache Airflow.

## Components

### 1. Data Sources
- **Salla API**: E-commerce platform API providing orders, customers, and products data
- **Authentication**: Bearer token-based authentication
- **Rate Limits**: Handled with exponential backoff and retry logic

### 2. Extraction Layer (Bronze)
- **Purpose**: Raw data ingestion from API
- **Technology**: Python with requests library
- **Features**:
  - Batch processing
  - Pagination handling
  - Error recovery
  - Audit trail (loaded_at, source_system)

### 3. Transformation Layer (Silver)
- **Purpose**: Data cleansing and standardization
- **Technology**: Python with pandas
- **Transformations**:
  - Null removal
  - Deduplication
  - Type conversion
  - JSON extraction
  - Calculated fields

### 4. Analytics Layer (Gold)
- **Purpose**: Business-ready dimensional model
- **Design**: Star schema
- **Components**:
  - Dimension tables (SCD Type 2)
  - Fact tables
  - Date dimension
  - Lookup dimensions

### 5. Orchestration
- **Technology**: Apache Airflow 2.8
- **DAGs**: Three separate DAGs for each layer
- **Scheduling**: Sequential execution with sensors
- **Features**:
  - Retry logic
  - Task dependencies
  - Parallel execution where possible
  - Monitoring and alerting

### 6. Data Warehouse
- **Technology**: Snowflake
- **Database**: SALLA_DWH
- **Schemas**: BRONZE, SILVER, GOLD
- **Features**:
  - Columnar storage
  - Auto-scaling
  - Query caching
  - Time travel

### 7. Visualization
- **Technology**: Power BI
- **Connection**: Direct query to Snowflake Gold layer
- **Optimization**: Star schema for fast queries

## Data Flow

```
┌─────────────┐
│  Salla API  │
└──────┬──────┘
       │ REST API (JSON)
       │
       ▼
┌─────────────────────────────┐
│  Bronze Layer (Raw)         │
│  - bronze_orders            │
│  - bronze_customers         │
│  - bronze_products          │
└──────────┬──────────────────┘
           │ ETL (Clean)
           │
           ▼
┌─────────────────────────────┐
│  Silver Layer (Cleaned)     │
│  - silver_orders            │
│  - silver_customers         │
│  - silver_products          │
└──────────┬──────────────────┘
           │ ETL (Dimension)
           │
           ▼
┌─────────────────────────────┐
│  Gold Layer (Analytics)     │
│  Dimensions:                │
│  - dim_customers            │
│  - dim_products             │
│  - dim_date                 │
│  - dim_payment_method       │
│  - dim_shipping_method      │
│  Facts:                     │
│  - fact_orders              │
│  - fact_order_items         │
└──────────┬──────────────────┘
           │ DirectQuery
           │
           ▼
┌─────────────────────────────┐
│  Power BI                   │
│  - Dashboards               │
│  - Reports                  │
│  - Analytics                │
└─────────────────────────────┘
```

## Airflow DAG Architecture

### Bronze DAG (salla_bronze_extraction)
```
┌────────────────────┐
│  Start             │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│  extract_orders    │◄───┤extract_customers   │◄───┤ extract_products   │
└────────────────────┘    └────────────────────┘    └────────────────────┘
          │                         │                         │
          └─────────────────────────┴─────────────────────────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │   End    │
                              └──────────┘
```

### Silver DAG (salla_silver_transformation)
```
┌────────────────────┐
│  Start             │
└─────────┬──────────┘
          │
          ▼
┌────────────────────────────┐
│ wait_for_bronze_extraction │
└─────────┬──────────────────┘
          │
          ▼
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│transform_orders    │◄───┤transform_customers │◄───┤transform_products  │
└────────────────────┘    └────────────────────┘    └────────────────────┘
          │                         │                         │
          └─────────────────────────┴─────────────────────────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │   End    │
                              └──────────┘
```

### Gold DAG (salla_gold_dimensional)
```
┌────────────────────┐
│  Start             │
└─────────┬──────────┘
          │
          ▼
┌──────────────────────────────┐
│wait_for_silver_transformation│
└─────────┬────────────────────┘
          │
          ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│load_dim  │  │load_dim  │  │load_dim  │  │load_dim  │  │load_dim  │
│_date     │  │_customers│  │_products │  │_payment  │  │_shipping │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │              │              │              │
     └─────────────┴──────────────┴──────────────┴──────────────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │load_fact_     │
                          │orders         │
                          └───────┬───────┘
                                  │
                                  ▼
                            ┌──────────┐
                            │   End    │
                            └──────────┘
```

## Error Handling Strategy

### API Level
1. Request timeout: 30 seconds
2. Retry attempts: 3 with exponential backoff
3. Rate limiting: Wait for Retry-After header
4. Failed requests: Log and raise exception

### Database Level
1. Connection pooling
2. Transaction management
3. Rollback on failure
4. Data validation before insert

### Airflow Level
1. Task retries: 2-3 times with delay
2. Task timeout: 1-2 hours
3. Email alerts on failure
4. XCom for inter-task communication

## Security Considerations

### Credentials Management
- Environment variables for sensitive data
- No hardcoded credentials
- .env file in .gitignore

### API Security
- Bearer token authentication
- HTTPS only
- Token rotation recommended

### Database Security
- Role-based access control (RBAC)
- Least privilege principle
- Encrypted connections
- IP whitelisting

### Data Privacy
- No PII in logs
- Secure data at rest
- Compliance with data protection regulations

## Performance Optimization

### Batch Processing
- Configurable batch size (default: 100)
- Parallel API calls where possible
- Bulk inserts to database

### Snowflake Optimization
- Clustering keys on frequently queried columns
- Materialized views for aggregations
- Query result caching
- Warehouse auto-suspend

### Airflow Optimization
- Task parallelism
- Worker scaling
- Connection pooling
- DAG serialization

## Disaster Recovery

### Backup Strategy
- Snowflake Time Travel (90 days)
- Fail-safe (7 days after Time Travel)
- Regular snapshots of Airflow metadata

### Recovery Procedures
1. Data corruption: Restore from Time Travel
2. Schema changes: Version control SQL scripts
3. Airflow failure: Restart from last successful task
4. API outage: Resume from last checkpoint

## Monitoring and Alerting

### Metrics to Monitor
- DAG run duration
- Task success/failure rates
- API response times
- Data volume trends
- Query performance
- Warehouse credit usage

### Alerts
- DAG failure
- Task retry exhaustion
- Data quality issues
- Unusual data volumes
- Performance degradation

## Scalability Roadmap

### Phase 1 (Current)
- 3 API endpoints
- Daily batch processing
- Single Airflow instance

### Phase 2 (Near Future)
- Additional API endpoints
- Hourly/real-time processing
- Multiple Airflow workers

### Phase 3 (Long Term)
- Multiple data sources
- Streaming integration
- Auto-scaling infrastructure
- Advanced analytics (ML/AI)
