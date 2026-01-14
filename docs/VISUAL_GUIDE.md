# Visual Documentation Guide

This guide provides visual representations of the ETL pipeline architecture, data flows, database schemas, and user interfaces.

---

## Table of Contents

1. [System Architecture Diagram](#system-architecture-diagram)
2. [Data Flow Visualization](#data-flow-visualization)
3. [Database Schema Diagrams](#database-schema-diagrams)
4. [Airflow UI Screenshots](#airflow-ui-screenshots)
5. [Power BI Integration](#power-bi-integration)
6. [Configuration Examples](#configuration-examples)

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SALLA API TO DATA WAREHOUSE                        │
│                              ETL PIPELINE ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Salla E-commerce  │  ◄─── Source System
│   REST API       │       (orders, customers, products)
└────────┬─────────┘
         │ HTTPS + Bearer Token Auth
         │ Batch Processing (100 records/page)
         │ Rate Limiting (429 handling)
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APACHE AIRFLOW                                     │
│                        (Orchestration Layer)                                │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │ Bronze DAG   │───▶│ Silver DAG   │───▶│  Gold DAG    │                 │
│  │ (2:00 AM)    │    │ (3:00 AM)    │    │ (4:00 AM)    │                 │
│  └──────────────┘    └──────────────┘    └──────────────┘                 │
│         │                    │                    │                         │
│         │  Extract           │  Transform         │  Load                   │
│         │  (Raw Data)        │  (Clean Data)      │  (Analytics)            │
└─────────┼────────────────────┼────────────────────┼─────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATABASE (Choose One)                                     │
│                                                                              │
│  ┌────────────────────────────┐      ┌────────────────────────────┐        │
│  │     SNOWFLAKE (Cloud)      │  OR  │  SQL SERVER (On-Premise)   │        │
│  │  ┌──────────────────────┐  │      │  ┌──────────────────────┐  │        │
│  │  │  BRONZE LAYER        │  │      │  │  BRONZE LAYER        │  │        │
│  │  │  • bronze_orders     │  │      │  │  • bronze_orders     │  │        │
│  │  │  • bronze_customers  │  │      │  │  • bronze_customers  │  │        │
│  │  │  • bronze_products   │  │      │  │  • bronze_products   │  │        │
│  │  └──────────────────────┘  │      │  └──────────────────────┘  │        │
│  │           │                 │      │           │                 │        │
│  │  ┌──────────────────────┐  │      │  ┌──────────────────────┐  │        │
│  │  │  SILVER LAYER        │  │      │  │  SILVER LAYER        │  │        │
│  │  │  • silver_orders     │  │      │  │  • silver_orders     │  │        │
│  │  │  • silver_customers  │  │      │  │  • silver_customers  │  │        │
│  │  │  • silver_products   │  │      │  │  • silver_products   │  │        │
│  │  └──────────────────────┘  │      │  └──────────────────────┘  │        │
│  │           │                 │      │           │                 │        │
│  │  ┌──────────────────────┐  │      │  ┌──────────────────────┐  │        │
│  │  │  GOLD LAYER          │  │      │  │  GOLD LAYER          │  │        │
│  │  │  Dimensions:         │  │      │  │  Dimensions:         │  │        │
│  │  │  • dim_customers     │  │      │  │  • dim_customers     │  │        │
│  │  │  • dim_products      │  │      │  │  • dim_products      │  │        │
│  │  │  • dim_date          │  │      │  │  • dim_date          │  │        │
│  │  │  Facts:              │  │      │  │  Facts:              │  │        │
│  │  │  • fact_orders       │  │      │  │  • fact_orders       │  │        │
│  │  │  • fact_order_items  │  │      │  │  • fact_order_items  │  │        │
│  │  └──────────────────────┘  │      │  └──────────────────────┘  │        │
│  └────────────────────────────┘      └────────────────────────────┘        │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               │ DirectQuery / Import
                               ▼
                    ┌─────────────────────┐
                    │    POWER BI         │
                    │  • Dashboards       │
                    │  • Reports          │
                    │  • Analytics        │
                    └─────────────────────┘
```

---

## Data Flow Visualization

### Bronze Layer Flow (Raw Data Ingestion)

```
┌──────────────┐
│  Salla API   │
└──────┬───────┘
       │
       │ 1. API Call (GET /orders?page=1&per_page=100)
       │    Headers: Authorization: Bearer <token>
       │
       ▼
┌─────────────────────────────┐
│  API Response (JSON)         │
│  {                           │
│    "data": [                 │
│      {                       │
│        "id": 12345,          │
│        "amount": 299.99,     │
│        "customer": {...},    │
│        "items": [...]        │
│      }                       │
│    ],                        │
│    "pagination": {           │
│      "hasMorePages": true    │
│    }                         │
│  }                           │
└──────────┬──────────────────┘
           │
           │ 2. Extract & Store Raw
           │    (No transformation)
           ▼
┌─────────────────────────────┐
│  Bronze Table                │
│  ┌─────────────────────────┐│
│  │ id: 12345               ││
│  │ reference_id: ORD-001   ││
│  │ amount: 299.99          ││
│  │ items: {...} (JSON)     ││
│  │ loaded_at: 2024-01-14   ││
│  │ source_system: SALLA_API││
│  └─────────────────────────┘│
└─────────────────────────────┘
```

### Silver Layer Flow (Data Cleansing)

```
┌─────────────────────────────┐
│  Bronze Table (Raw)          │
│  • JSON fields               │
│  • Nulls present             │
│  • Inconsistent formats      │
└──────────┬──────────────────┘
           │
           │ 3. Transform & Cleanse
           │    • Extract JSON fields
           │    • Remove nulls
           │    • Standardize formats
           │    • Calculate metrics
           ▼
┌─────────────────────────────┐
│  Transformation Logic        │
│  ┌─────────────────────────┐│
│  │ • Parse JSON            ││
│  │ • Extract city/country  ││
│  │ • Calculate age_group   ││
│  │ • Compute profit_margin ││
│  │ • Deduplicate records   ││
│  └─────────────────────────┘│
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Silver Table (Clean)        │
│  ┌─────────────────────────┐│
│  │ order_id: 12345         ││
│  │ customer_name: John Doe ││
│  │ shipping_city: Riyadh   ││
│  │ total_amount: 299.99    ││
│  │ items_count: 3          ││
│  │ processed_at: 2024-01-14││
│  └─────────────────────────┘│
└─────────────────────────────┘
```

### Gold Layer Flow (Dimensional Model)

```
┌─────────────────────────────┐
│  Silver Tables (Clean)       │
│  • silver_orders             │
│  • silver_customers          │
│  • silver_products           │
└──────────┬──────────────────┘
           │
           │ 4. Build Dimensional Model
           │    • Create dimensions (SCD Type 2)
           │    • Build fact tables
           │    • Establish relationships
           ▼
┌───────────────────────────────────────────────────────────┐
│                    GOLD LAYER (Star Schema)                │
│                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ dim_customers│    │ dim_products │    │  dim_date  │  │
│  ├──────────────┤    ├──────────────┤    ├────────────┤  │
│  │customer_key  │    │product_key   │    │date_key    │  │
│  │customer_id   │    │product_id    │    │full_date   │  │
│  │full_name     │    │product_name  │    │month_name  │  │
│  │email         │    │sku           │    │quarter     │  │
│  │country       │    │price         │    │year        │  │
│  │is_current    │    │is_current    │    │is_weekend  │  │
│  └──────┬───────┘    └──────┬───────┘    └─────┬──────┘  │
│         │                   │                   │         │
│         └───────────────────┼───────────────────┘         │
│                             │                             │
│                    ┌────────▼────────┐                    │
│                    │  fact_orders    │                    │
│                    ├─────────────────┤                    │
│                    │order_key  (PK)  │                    │
│                    │customer_key (FK)│                    │
│                    │order_date_key(FK)│                   │
│                    │product_key (FK) │                    │
│                    │total_amount     │                    │
│                    │quantity         │                    │
│                    └─────────────────┘                    │
└───────────────────────────────────────────────────────────┘
```

---

## Database Schema Diagrams

### Bronze Layer Schema

```
┌─────────────────────────────────────────────────────────────┐
│                    bronze_orders                             │
├─────────────────────────────────────────────────────────────┤
│ PK  id                      BIGINT                           │
│     reference_id            VARCHAR(100)                     │
│     status                  VARCHAR(50)                      │
│     amount                  FLOAT                            │
│     customer_id             BIGINT                           │
│     customer_name           NVARCHAR(255)                    │
│     customer_email          NVARCHAR(255)                    │
│     payment_method          VARCHAR(100)                     │
│     shipping_address        NVARCHAR(MAX) -- JSON           │
│     items                   NVARCHAR(MAX) -- JSON           │
│     created_at              DATETIME2                        │
│     loaded_at               DATETIME2                        │
│     source_system           VARCHAR(50)                      │
└─────────────────────────────────────────────────────────────┘
         Indexes:
         • idx_bronze_orders_customer (customer_id)
         • idx_bronze_orders_created (created_at)
         • idx_bronze_orders_status (status)

┌─────────────────────────────────────────────────────────────┐
│                  bronze_customers                            │
├─────────────────────────────────────────────────────────────┤
│ PK  id                      BIGINT                           │
│     first_name              NVARCHAR(255)                    │
│     last_name               NVARCHAR(255)                    │
│     email                   NVARCHAR(255)                    │
│     mobile                  VARCHAR(50)                      │
│     country                 NVARCHAR(100)                    │
│     city                    NVARCHAR(100)                    │
│     addresses               NVARCHAR(MAX) -- JSON           │
│     created_at              DATETIME2                        │
│     loaded_at               DATETIME2                        │
└─────────────────────────────────────────────────────────────┘
```

### Silver Layer Schema

```
┌─────────────────────────────────────────────────────────────┐
│                    silver_orders                             │
├─────────────────────────────────────────────────────────────┤
│ PK  order_id                BIGINT                           │
│     reference_id            VARCHAR(100)                     │
│     order_status            VARCHAR(50)                      │
│     order_date              DATETIME2                        │
│     customer_id             BIGINT                           │
│     customer_name           NVARCHAR(255)                    │
│     shipping_country        NVARCHAR(100)  -- Extracted     │
│     shipping_city           NVARCHAR(100)  -- Extracted     │
│     subtotal_amount         FLOAT                            │
│     discount_amount         FLOAT                            │
│     tax_amount              FLOAT                            │
│     total_amount            FLOAT                            │
│     items_count             INT            -- Calculated     │
│     processed_at            DATETIME2                        │
└─────────────────────────────────────────────────────────────┘
         Indexes:
         • idx_silver_orders_customer (customer_id)
         • idx_silver_orders_date (order_date)

┌─────────────────────────────────────────────────────────────┐
│                  silver_customers                            │
├─────────────────────────────────────────────────────────────┤
│ PK  customer_id             BIGINT                           │
│     full_name               NVARCHAR(500)  -- Computed      │
│     first_name              NVARCHAR(255)                    │
│     email                   NVARCHAR(255)                    │
│     country                 NVARCHAR(100)                    │
│     age_group               VARCHAR(50)    -- Computed      │
│     customer_status         VARCHAR(50)                      │
│     processed_at            DATETIME2                        │
└─────────────────────────────────────────────────────────────┘
```

### Gold Layer Schema (Star Schema)

```
                    ┌──────────────────────┐
                    │   dim_customers      │
                    ├──────────────────────┤
                    │PK customer_key       │
                    │  customer_id         │
                    │  full_name           │
                    │  email               │
                    │  country             │
                    │  effective_date      │  SCD Type 2
                    │  expiration_date     │  ◄──────────
                    │  is_current          │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼────────────────────┐
        │                      │                    │
┌───────▼─────────┐   ┌────────▼───────┐   ┌───────▼────────┐
│  dim_date       │   │ fact_orders    │   │ dim_products   │
├─────────────────┤   ├────────────────┤   ├────────────────┤
│PK date_key      │   │PK order_key    │   │PK product_key  │
│  full_date      │   │FK customer_key │   │  product_id    │
│  day_name       │   │FK order_date_key   │  product_name  │
│  month_name     │   │FK product_key  │   │  sku           │
│  quarter        │   │  order_status  │   │  regular_price │
│  year           │   │  quantity      │   │  effective_date│
│  is_weekend     │   │  total_amount  │   │  is_current    │
└─────────────────┘   └────────────────┘   └────────────────┘
```

---

## Airflow UI Screenshots

### 1. DAGs Overview Page

```
┌─────────────────────────────────────────────────────────────────────┐
│ Apache Airflow                                          Admin ▼     │
├─────────────────────────────────────────────────────────────────────┤
│ DAGs  │  Security  │  Browse  │  Admin  │  Docs                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Search DAGs: [____________]  [Refresh]                              │
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │ DAG Name                 │ Owner   │ Schedule │ Last Run │ ●  │   │
│ ├──────────────────────────────────────────────────────────────┤   │
│ │ salla_bronze_extraction  │ airflow │ 0 2 * * *│ Success  │ ●  │   │
│ │ salla_silver_transformation│airflow│ 0 3 * * *│ Success  │ ●  │   │
│ │ salla_gold_dimensional   │ airflow │ 0 4 * * *│ Success  │ ●  │   │
│ └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│ Status Legend:                                                       │
│ ● Green  = Success                                                   │
│ ● Yellow = Running                                                   │
│ ● Red    = Failed                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Bronze DAG Graph View

```
┌─────────────────────────────────────────────────────────────────────┐
│ salla_bronze_extraction                              [Graph View]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                          [Start]                                     │
│                             │                                        │
│              ┌──────────────┼──────────────┐                        │
│              │              │              │                        │
│              ▼              ▼              ▼                        │
│    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│    │  extract_   │ │  extract_   │ │  extract_   │                │
│    │  orders     │ │  customers  │ │  products   │                │
│    │  [Success]  │ │  [Success]  │ │  [Success]  │                │
│    └─────────────┘ └─────────────┘ └─────────────┘                │
│              │              │              │                        │
│              └──────────────┼──────────────┘                        │
│                             │                                        │
│                          [End]                                       │
│                                                                      │
│ Run Duration: 5m 23s                                                │
│ Records Processed: Orders: 1,234 | Customers: 567 | Products: 89   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Silver DAG with External Sensor

```
┌─────────────────────────────────────────────────────────────────────┐
│ salla_silver_transformation                      [Graph View]        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                          [Start]                                     │
│                             │                                        │
│                             ▼                                        │
│                  ┌──────────────────────┐                           │
│                  │ wait_for_bronze_     │                           │
│                  │ extraction           │                           │
│                  │ [Success]            │  ◄── External Task Sensor │
│                  └──────────────────────┘                           │
│                             │                                        │
│              ┌──────────────┼──────────────┐                        │
│              │              │              │                        │
│              ▼              ▼              ▼                        │
│    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│    │ transform_  │ │ transform_  │ │ transform_  │                │
│    │ orders      │ │ customers   │ │ products    │                │
│    │ [Success]   │ │ [Success]   │ │ [Success]   │                │
│    └─────────────┘ └─────────────┘ └─────────────┘                │
│              │              │              │                        │
│              └──────────────┼──────────────┘                        │
│                             │                                        │
│                          [End]                                       │
│                                                                      │
│ Data Quality Checks: ✓ Passed                                       │
│ Null Percentage: 0.5% | Duplicates: 0                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 4. Task Log Example

```
┌─────────────────────────────────────────────────────────────────────┐
│ Task: extract_orders                                [View Logs]      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ [2024-01-14 02:00:15] INFO - Starting orders extraction             │
│ [2024-01-14 02:00:16] INFO - Connecting to Salla API                │
│ [2024-01-14 02:00:17] INFO - Fetching orders page 1                 │
│ [2024-01-14 02:00:18] INFO - Fetched 100 orders from page 1         │
│ [2024-01-14 02:00:19] INFO - Fetching orders page 2                 │
│ [2024-01-14 02:00:20] INFO - Fetched 100 orders from page 2         │
│ ...                                                                  │
│ [2024-01-14 02:05:10] INFO - Fetched total of 1,234 orders          │
│ [2024-01-14 02:05:11] INFO - Loading to SQL Server Bronze layer     │
│ [2024-01-14 02:05:38] INFO - Successfully loaded 1,234 records      │
│ [2024-01-14 02:05:39] INFO - Task completed successfully            │
│                                                                      │
│ Exit Code: 0                                                         │
│ Duration: 5m 23s                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Power BI Integration

### 1. Power BI Connection Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│ Get Data                                                    [×]      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Search: [SQL Server________]                                        │
│                                                                      │
│ All                                                                  │
│ ├─ Database                                                          │
│ │  ├─ SQL Server  ◄── Selected                                     │
│ │  ├─ Snowflake                                                     │
│ │  ├─ Oracle                                                        │
│ │  └─ ...                                                           │
│                                                                      │
│ ┌─────────────────────────────────────────────────────────────┐    │
│ │ SQL Server Connection                                        │    │
│ │                                                              │    │
│ │ Server:    localhost                                         │    │
│ │ Database:  SALLA_DWH                                         │    │
│ │                                                              │    │
│ │ Data Connectivity mode:                                      │    │
│ │ ○ Import                                                     │    │
│ │ ● DirectQuery  ◄── For real-time data                       │    │
│ │                                                              │    │
│ │ Advanced options:                                            │    │
│ │ SQL statement (optional): SELECT * FROM gold.vw_daily_sales  │    │
│ │                                                              │    │
│ │                                    [OK]     [Cancel]         │    │
│ └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Power BI Navigator (Table Selection)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Navigator                                                   [×]      │
├─────────────────────────────────────────────────────────────────────┤
│ Display Options: ☑ Enable data preview                              │
│                                                                      │
│ ┌──────────────────────┐  ┌────────────────────────────────────┐   │
│ │ SALLA_DWH           │  │ Preview: gold.gold_fact_orders      │   │
│ │ ├─ bronze           │  ├─────────────────────────────────────┤   │
│ │ ├─ silver           │  │order_key│customer_key│total_amount│   │
│ │ └─ gold             │  ├─────────────────────────────────────┤   │
│ │    ├─☑dim_customers │  │  1001   │    501     │  299.99    │   │
│ │    ├─☑dim_products  │  │  1002   │    502     │  450.00    │   │
│ │    ├─☑dim_date      │  │  1003   │    501     │  125.50    │   │
│ │    ├─☑fact_orders   │  │  1004   │    503     │  890.00    │   │
│ │    └─☑fact_order_   │  │  ...    │    ...     │  ...       │   │
│ │       items         │  └────────────────────────────────────┘   │
│ └──────────────────────┘                                            │
│                                                                      │
│ Relationships will be auto-detected based on foreign keys           │
│                                                                      │
│                               [Load]  [Transform Data]  [Cancel]    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Power BI Data Model View

```
┌─────────────────────────────────────────────────────────────────────┐
│ Model View                                          [Relationships]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐                                                │
│  │ dim_customers   │                                                │
│  ├─────────────────┤                                                │
│  │●customer_key    │────────────┐                                   │
│  │ customer_id     │            │                                   │
│  │ full_name       │            │                                   │
│  │ email           │            │  1:Many                           │
│  │ country         │            │                                   │
│  └─────────────────┘            │                                   │
│                                  │                                   │
│  ┌─────────────────┐            │      ┌─────────────────┐         │
│  │ dim_date        │            │      │ fact_orders     │         │
│  ├─────────────────┤            │      ├─────────────────┤         │
│  │●date_key        │────────────┼──────│●order_key       │         │
│  │ full_date       │            │      │ customer_key    │◄────────┤
│  │ month_name      │            │      │ order_date_key  │◄────────┤
│  │ quarter         │            │      │ product_key     │◄────────┤
│  │ year            │            │      │ total_amount    │         │
│  └─────────────────┘            │      │ quantity        │         │
│                                  │      └─────────────────┘         │
│  ┌─────────────────┐            │                                   │
│  │ dim_products    │            │                                   │
│  ├─────────────────┤            │                                   │
│  │●product_key     │────────────┘                                   │
│  │ product_id      │                                                │
│  │ product_name    │                                                │
│  │ sku             │                                                │
│  │ price           │                                                │
│  └─────────────────┘                                                │
│                                                                      │
│  Relationships: 4 active                                             │
│  ● = Primary Key | Foreign Key relationships shown with arrows      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4. Power BI Dashboard Example

```
┌─────────────────────────────────────────────────────────────────────┐
│ Sales Dashboard                                     [Refresh] [○]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ┌──────────────────────┐  ┌──────────────────────┐                 │
│ │ Total Sales          │  │ Total Orders         │                 │
│ │                      │  │                      │                 │
│ │   SAR 1,234,567     │  │      5,432           │                 │
│ │   ▲ 15.3% vs LM     │  │      ▲ 8.7% vs LM    │                 │
│ └──────────────────────┘  └──────────────────────┘                 │
│                                                                      │
│ ┌─────────────────────────────────────────────────────────────┐    │
│ │ Sales Trend by Month                                         │    │
│ │ 150K│                                              ███       │    │
│ │     │                                    ███       ███       │    │
│ │ 100K│                          ███       ███  ███  ███       │    │
│ │     │                ███       ███  ███  ███  ███  ███       │    │
│ │  50K│      ███  ███  ███  ███  ███  ███  ███  ███  ███       │    │
│ │     └────────────────────────────────────────────────────── │    │
│ │      Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct       │    │
│ └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│ ┌────────────────────────┐  ┌──────────────────────────────┐       │
│ │ Top 5 Customers        │  │ Sales by City                 │       │
│ │ 1. Ahmed Al-Saud 45K  │  │ Riyadh    ████████████ 450K  │       │
│ │ 2. Mohammed Ali  38K  │  │ Jeddah    ██████████ 320K    │       │
│ │ 3. Fatima Hassan 32K  │  │ Dammam    ████████ 210K      │       │
│ │ 4. Omar Khalid   28K  │  │ Mecca     ██████ 180K        │       │
│ │ 5. Sara Abdullah 24K  │  │ Other     ████ 110K          │       │
│ └────────────────────────┘  └──────────────────────────────┘       │
│                                                                      │
│ Last Refreshed: 2024-01-14 09:30 AM                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Examples

### 1. Environment File (.env)

```
┌─────────────────────────────────────────────────────────────────────┐
│ .env Configuration File                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ # ========================================                           │
│ # DATABASE SELECTION                                                │
│ # ========================================                           │
│ DATABASE_TYPE=sqlserver          ◄── Choose: snowflake or sqlserver│
│                                                                      │
│ # ========================================                           │
│ # SALLA API CONFIGURATION                                           │
│ # ========================================                           │
│ SALLA_API_BASE_URL=https://api.salla.dev/admin/v2                  │
│ SALLA_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...          │
│ API_BATCH_SIZE=100                                                  │
│                                                                      │
│ # ========================================                           │
│ # SQL SERVER (ON-PREMISE)                                           │
│ # ========================================                           │
│ SQLSERVER_HOST=192.168.1.100     ◄── Your Windows laptop IP       │
│ SQLSERVER_PORT=1433                                                 │
│ SQLSERVER_DATABASE=SALLA_DWH                                        │
│ SQLSERVER_TRUSTED_CONNECTION=True ◄── Windows Authentication       │
│ # For SQL Auth, set to False and provide:                          │
│ # SQLSERVER_USER=etl_user                                          │
│ # SQLSERVER_PASSWORD=your_password                                 │
│                                                                      │
│ # ========================================                           │
│ # SNOWFLAKE (CLOUD) - Alternative                                  │
│ # ========================================                           │
│ # SNOWFLAKE_ACCOUNT=your_account.region                            │
│ # SNOWFLAKE_USER=your_username                                     │
│ # SNOWFLAKE_PASSWORD=your_password                                 │
│ # SNOWFLAKE_WAREHOUSE=COMPUTE_WH                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. SQL Server Management Studio View

```
┌─────────────────────────────────────────────────────────────────────┐
│ Microsoft SQL Server Management Studio                              │
├─────────────────────────────────────────────────────────────────────┤
│ File  Edit  View  Query  Tools  Window  Help                        │
├──────────┬──────────────────────────────────────────────────────────┤
│ Object   │                                                           │
│ Explorer │  Query: SQLQuery1.sql                                    │
│          │                                                           │
│ ├─📁 SQLSERVER01                                                     │
│ │ ├─📁 Databases                                                     │
│ │ │ ├─📁 SALLA_DWH  ◄── Your Data Warehouse                         │
│ │ │ │ ├─📁 Tables                                                    │
│ │ │ │ │ ├─📁 bronze                                                 │
│ │ │ │ │ │ ├─📊 bronze_orders (1,234 rows)                          │
│ │ │ │ │ │ ├─📊 bronze_customers (567 rows)                         │
│ │ │ │ │ │ └─📊 bronze_products (89 rows)                           │
│ │ │ │ │ ├─📁 silver                                                 │
│ │ │ │ │ │ ├─📊 silver_orders (1,234 rows)                          │
│ │ │ │ │ │ ├─📊 silver_customers (567 rows)                         │
│ │ │ │ │ │ └─📊 silver_products (89 rows)                           │
│ │ │ │ │ └─📁 gold                                                   │
│ │ │ │ │   ├─📊 gold_dim_customers (567 rows)                       │
│ │ │ │ │   ├─📊 gold_dim_products (89 rows)                         │
│ │ │ │ │   ├─📊 gold_dim_date (3,652 rows)                          │
│ │ │ │ │   ├─📊 gold_fact_orders (1,234 rows)                       │
│ │ │ │ │   └─📊 gold_fact_order_items (3,456 rows)                  │
│ │ │ │ └─📁 Security                                                 │
│          │                                                           │
│          │  Results:                                                 │
│          │  ┌────────────────────────────────────────────────┐      │
│          │  │ layer     │ table_name        │ row_count     │      │
│          │  ├────────────────────────────────────────────────┤      │
│          │  │ Bronze    │ bronze_orders     │ 1,234         │      │
│          │  │ Silver    │ silver_orders     │ 1,234         │      │
│          │  │ Gold      │ gold_fact_orders  │ 1,234         │      │
│          │  └────────────────────────────────────────────────┘      │
│          │                                                           │
└──────────┴───────────────────────────────────────────────────────────┘
```

---

## Incremental Loading Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│              INCREMENTAL LOADING PROCESS                             │
└─────────────────────────────────────────────────────────────────────┘

Day 1 - Initial Load (Full)
─────────────────────────────
┌──────────────┐
│ API: 10,000  │
│ total orders │
└──────┬───────┘
       │
       │ Load ALL
       ▼
┌──────────────────┐
│ Database:        │
│ 10,000 orders    │
│                  │
│ Watermark Table: │
│ last_loaded:     │
│ 2024-01-14       │
└──────────────────┘


Day 2 - Incremental Load (Delta Only)
──────────────────────────────────────
┌──────────────┐
│ API: 10,100  │ ◄── 100 new orders
│ total orders │
└──────┬───────┘
       │
       │ Query: WHERE created_at > '2024-01-14'
       │ Load ONLY 100 new orders
       ▼
┌──────────────────┐
│ Database:        │
│ 10,100 orders    │ ◄── Added 100 orders
│                  │
│ Watermark Table: │
│ last_loaded:     │
│ 2024-01-15       │ ◄── Updated
└──────────────────┘


Benefits:
✓ Fast: Only loads new/changed data
✓ Efficient: Reduces API calls and database load
✓ Scalable: Performance doesn't degrade over time
```

---

## Summary

This visual guide demonstrates:

1. **System Architecture** - How components interact
2. **Data Flow** - Step-by-step transformation process
3. **Database Schemas** - Structure of Bronze, Silver, Gold layers
4. **Airflow UI** - What you'll see when running DAGs
5. **Power BI Integration** - How to connect and visualize
6. **Configuration** - How to set up the system

All visualizations use text-based diagrams that work in any text editor or documentation viewer.

---

For actual screenshot examples with your data:
1. Set up the system following `docs/QUICKSTART.md` or `docs/SQLSERVER_MIGRATION.md`
2. Run the DAGs in Airflow
3. Take screenshots of your Airflow UI, SQL Server Management Studio, and Power BI
4. Replace these text diagrams with your actual screenshots

The system will look exactly as diagrammed above, with your actual data and configurations!
