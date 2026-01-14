# Quick Start Guide

This guide will help you get the Salla to Snowflake ETL pipeline up and running quickly.

## Prerequisites Checklist

- [ ] Python 3.8 or higher installed
- [ ] Snowflake account with credentials
- [ ] Salla API bearer token
- [ ] 2GB+ available RAM
- [ ] Stable internet connection

## Step-by-Step Setup (15 minutes)

### Step 1: Clone and Setup Environment (3 minutes)

```bash
# Clone the repository
git clone https://github.com/MUSTAQ-AHAMMAD/sql-data-warehouse-project.git
cd sql-data-warehouse-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables (2 minutes)

```bash
# Copy the example file
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

Update these critical values in `.env`:

```bash
SALLA_API_TOKEN=your_actual_bearer_token_here
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
```

### Step 3: Validate Installation (1 minute)

```bash
python src/utils/validate_installation.py
```

If all checks pass, proceed to the next step.

### Step 4: Setup Snowflake Database (2 minutes)

```bash
python src/utils/setup_database.py
```

This creates all necessary databases, schemas, and tables.

### Step 5: Generate Sample Data (Optional - 1 minute)

For testing without actual API credentials:

```bash
python src/utils/sample_data_generator.py
```

### Step 6: Configure Airflow (5 minutes)

```bash
# Set Airflow home
export AIRFLOW_HOME=$(pwd)/airflow

# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

# Link DAGs
mkdir -p $AIRFLOW_HOME/dags
cp -r dags/* $AIRFLOW_HOME/dags/
```

### Step 7: Start Airflow (1 minute)

Open two terminal windows:

**Terminal 1 - Webserver:**
```bash
source venv/bin/activate
airflow webserver --port 8080
```

**Terminal 2 - Scheduler:**
```bash
source venv/bin/activate
airflow scheduler
```

### Step 8: Run the Pipeline

1. Open browser: `http://localhost:8080`
2. Login with username: `admin`, password: `admin`
3. Enable these DAGs:
   - `salla_bronze_extraction`
   - `salla_silver_transformation`
   - `salla_gold_dimensional`
4. Click the play button on `salla_bronze_extraction` to trigger

## Testing the Pipeline

### Option 1: Through Airflow (Recommended)

1. Trigger Bronze DAG
2. Wait for completion (check Graph view)
3. Silver and Gold DAGs will run automatically on schedule

### Option 2: Direct Python Execution

```bash
# Test individual components
python src/api/salla_connector.py
python src/database/snowflake_connector.py
python src/transformations/bronze_extractor.py
```

## Verify Data in Snowflake

```sql
-- Connect to Snowflake and run:
USE DATABASE SALLA_DWH;

-- Check Bronze layer
SELECT COUNT(*) FROM BRONZE.bronze_orders;
SELECT COUNT(*) FROM BRONZE.bronze_customers;
SELECT COUNT(*) FROM BRONZE.bronze_products;

-- Check Silver layer
SELECT COUNT(*) FROM SILVER.silver_orders;
SELECT COUNT(*) FROM SILVER.silver_customers;
SELECT COUNT(*) FROM SILVER.silver_products;

-- Check Gold layer
SELECT COUNT(*) FROM GOLD.gold_fact_orders;
SELECT COUNT(*) FROM GOLD.gold_dim_customers;
SELECT COUNT(*) FROM GOLD.gold_dim_products;
```

## Connect Power BI

1. Open Power BI Desktop
2. Get Data → Snowflake
3. Server: `your_account.region.snowflakecomputing.com`
4. Database: `SALLA_DWH`
5. Select GOLD schema tables
6. Load and create visualizations

## Troubleshooting

### Issue: Airflow DAGs not showing

**Solution:**
```bash
# Check for errors in DAG files
python -m py_compile dags/*.py

# Refresh Airflow
airflow dags list
```

### Issue: Snowflake connection failed

**Solution:**
- Verify credentials in `.env`
- Test connection:
```python
from src.database.snowflake_connector import SnowflakeConnector
with SnowflakeConnector() as sf:
    print(sf.execute_query("SELECT CURRENT_VERSION()"))
```

### Issue: API rate limiting

**Solution:**
- Reduce batch size in `.env`:
```bash
API_BATCH_SIZE=50
API_RETRY_DELAY=10
```

### Issue: Out of memory

**Solution:**
- Process smaller batches
- Increase system RAM
- Use pagination more aggressively

## Next Steps

1. **Schedule Regular Runs**: DAGs are set to run daily at 2 AM, 3 AM, and 4 AM
2. **Monitor**: Check Airflow UI for task status and logs
3. **Optimize**: Adjust batch sizes and schedules based on data volume
4. **Scale**: Add more API endpoints following the pattern in existing code

## Getting Help

- Check logs in Airflow UI
- Review `docs/ARCHITECTURE.md` for system design
- Check `README.md` for detailed documentation
- Open GitHub issue for bugs or questions

## Daily Operations

Once set up, the pipeline runs automatically:

- **2:00 AM**: Bronze extraction from Salla API
- **3:00 AM**: Silver transformation
- **4:00 AM**: Gold dimensional model update
- **Morning**: Fresh data available in Power BI

Monitor through Airflow UI at `http://localhost:8080`

---

**Success!** You now have a fully operational data warehouse pipeline. 🎉
