# Health Monitoring Dashboard Guide

## Overview
The Health Monitoring Dashboard provides real-time visibility into your Salla Data Warehouse infrastructure. It monitors database connectivity, API status, data layer health, and ETL pipeline execution.

## Features
- 🏥 **Real-time Health Monitoring**: Auto-refreshes every 10 seconds
- 💾 **Database Status**: Connection health and version information
- 🌐 **API Status**: Salla API connectivity and configuration
- 📊 **Data Layer Metrics**: Bronze, Silver, and Gold layer row counts
- ⚙️ **ETL Pipeline Tracking**: Last run statistics and watermark information
- 📈 **Data Warehouse Statistics**: Comprehensive metrics across all layers

## Starting the Dashboard

### Method 1: Direct Python Execution
```bash
cd /path/to/sql-data-warehouse-project
python monitoring/health_dashboard.py
```

### Method 2: Using Environment Variables
```bash
export MONITORING_PORT=5001
export MONITORING_HOST=0.0.0.0
export MONITORING_DEBUG=False
python monitoring/health_dashboard.py
```

### Method 3: As a Background Service (Linux/Mac)
```bash
nohup python monitoring/health_dashboard.py > monitoring.log 2>&1 &
```

### Method 4: As a Windows Service
```powershell
# Using PowerShell
Start-Process python -ArgumentList "monitoring/health_dashboard.py" -WindowStyle Hidden
```

## Accessing the Dashboard

Once started, access the dashboard at:
```
http://localhost:5001
```

Or from another machine (if MONITORING_HOST is set to 0.0.0.0):
```
http://<your-server-ip>:5001
```

## Dashboard Components

### 1. Overall System Status
Displays the overall health status of your data warehouse:
- **Healthy**: All components operational ✅
- **Warning**: Some components not configured or have minor issues ⚠️
- **Unhealthy**: Critical component failures ❌

### 2. Database Card
Shows database connectivity and configuration:
- Connection status
- Database type (SQL Server or Snowflake)
- Version information
- Timestamp of last check

### 3. Salla API Card
Displays API integration status:
- Connection status
- Base URL
- Configuration state
- Token validation

### 4. Data Layers Card
Shows record counts for each layer:
- **Bronze Layer**: Raw data from API
  - Orders count
  - Customers count
  - Products count
- **Silver Layer**: Cleaned and transformed data
  - Orders count
  - Customers count
  - Products count
- **Gold Layer**: Dimensional model
  - Dimension customers count
  - Dimension products count
  - Fact orders count

### 5. ETL Pipeline Card
Displays ETL execution metrics:
- Last load timestamp for each entity
- Records loaded per entity
- Load duration
- Load rate (records per second)

### 6. Data Warehouse Statistics
Comprehensive metrics including:
- Total records in each layer
- Total sales amount
- Average order value
- Visual cards for easy monitoring

## REST API Endpoints

The dashboard also provides REST API endpoints:

### Get Health Status
```bash
curl http://localhost:5001/api/health
```

Returns JSON with complete health information:
```json
{
  "overall_status": "healthy",
  "database": {
    "status": "healthy",
    "message": "Connected to SQLSERVER",
    "details": {...}
  },
  "api": {...},
  "data_layers": {...},
  "etl_pipeline": {...},
  "timestamp": "2024-01-15T10:30:00"
}
```

### Get Statistics
```bash
curl http://localhost:5001/api/stats
```

Returns JSON with detailed statistics:
```json
{
  "status": "success",
  "statistics": {
    "bronze_orders": 1000,
    "silver_orders": 950,
    "gold_fact_orders": 900,
    "total_sales": 150000.50,
    "avg_order_value": 166.67
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

## Configuration

### Environment Variables

Configure the dashboard using `.env` file or environment variables:

```bash
# Dashboard Configuration
MONITORING_HOST=0.0.0.0          # Host to bind to (0.0.0.0 for all interfaces)
MONITORING_PORT=5001             # Port to run on
MONITORING_DEBUG=False           # Enable Flask debug mode

# Database Configuration
DATABASE_TYPE=sqlserver          # Database type
SQLSERVER_HOST=localhost\SQLEXPRESS
SQLSERVER_DATABASE=SALLA_DWH

# API Configuration
SALLA_API_TOKEN=your_token_here
SALLA_API_BASE_URL=https://api.salla.dev/admin/v2
```

## Running the Complete Pipeline

The complete pipeline orchestrator executes the end-to-end data warehouse pipeline:

### Basic Usage
```bash
# Using sample data (no API required)
python run_complete_pipeline.py --sample

# Using Salla API (requires configured token)
python run_complete_pipeline.py

# Force API usage (will fail if token not configured)
python run_complete_pipeline.py --no-sample
```

### Pipeline Phases
1. **Pre-flight Checks**: Validates database, tables, and API
2. **Bronze Extraction**: Pulls data from API or generates sample data
3. **Silver Transformation**: Cleanses and transforms Bronze data
4. **Gold Transformation**: Creates dimensional model
5. **Power BI Views**: Creates optimized reporting views
6. **Data Quality Verification**: Validates data integrity

### Pipeline Output
The orchestrator provides comprehensive logging:
```
================================================================================
🚀 STARTING COMPLETE DATA WAREHOUSE PIPELINE
================================================================================
Start Time: 2024-01-15 10:30:00
Database: SQLSERVER
Data Mode: SAMPLE DATA
================================================================================

... [detailed phase execution logs] ...

================================================================================
📊 PIPELINE EXECUTION SUMMARY
================================================================================

⏱️ Execution Time: 45.23 seconds

📥 Bronze Layer:
   Orders: 200
   Customers: 100
   Products: 50

🔄 Silver Layer:
   Orders: 200
   Customers: 100
   Products: 50

⭐ Gold Layer:
   Dimensions: 150
   Facts: 200

📊 Power BI:
   Views Created: 4

✅ No errors encountered

================================================================================
🎉 PIPELINE EXECUTION COMPLETE
================================================================================
```

## Troubleshooting

### Dashboard Won't Start

**Problem**: Port already in use
```
OSError: [WinError 10048] Only one usage of each socket address
```

**Solution**: Change the port or stop the conflicting service
```bash
# Use different port
export MONITORING_PORT=5002
python monitoring/health_dashboard.py
```

### Database Connection Failed

**Problem**: Cannot connect to database
```
❌ Database connection failed: Unable to connect
```

**Solutions**:
1. Check SQL Server service is running
2. Verify connection details in `.env`
3. Test connection using `test_connection.py`
4. Check Windows Authentication settings

### API Not Configured

**Problem**: API status shows "not_configured"

**Solution**: Set the API token in `.env`
```bash
SALLA_API_TOKEN=your_actual_token_here
```

Or use sample data mode:
```bash
python run_complete_pipeline.py --sample
```

### Empty Data Layers

**Problem**: All layer counts show 0

**Solutions**:
1. Run the complete pipeline first:
   ```bash
   python run_complete_pipeline.py --sample
   ```
2. Check database tables exist:
   ```bash
   python src/utils/setup_database.py
   ```

### Auto-Refresh Not Working

**Problem**: Dashboard doesn't auto-refresh

**Solutions**:
1. Check browser console for JavaScript errors
2. Ensure `/api/health` endpoint is accessible
3. Try manual refresh (F5)
4. Check CORS settings if accessing from different domain

## Integration with Other Tools

### Monitoring with Prometheus
Export metrics from the REST API:
```python
import requests
response = requests.get('http://localhost:5001/api/stats')
metrics = response.json()['statistics']
```

### Alerting with Scripts
Create alert scripts based on health status:
```bash
#!/bin/bash
HEALTH=$(curl -s http://localhost:5001/api/health | jq -r '.overall_status')
if [ "$HEALTH" != "healthy" ]; then
    echo "Alert: Data warehouse unhealthy!"
    # Send email, Slack notification, etc.
fi
```

### Dashboard as Windows Scheduled Task
Create a task to auto-start the dashboard on boot:
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: "At system startup"
4. Action: "Start a program"
5. Program: `python.exe`
6. Arguments: `C:\path\to\monitoring\health_dashboard.py`

## Best Practices

1. **Keep Dashboard Running**: Run as a service for continuous monitoring
2. **Regular Pipeline Execution**: Schedule `run_complete_pipeline.py` with cron/Task Scheduler
3. **Monitor Logs**: Check `monitoring.log` for issues
4. **Set Alerts**: Create scripts to alert on unhealthy status
5. **Resource Monitoring**: Monitor server resources (CPU, RAM, disk)
6. **Security**: Don't expose dashboard publicly without authentication
7. **Backup Configuration**: Keep `.env` backed up securely

## Advanced Configuration

### Custom Refresh Interval
Modify the JavaScript in `health_dashboard.html`:
```javascript
// Change from 10 seconds to 30 seconds
setInterval(updateDashboard, 30000);
```

### Add Authentication
Wrap the Flask app with authentication middleware:
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Implement your authentication logic
    return username == 'admin' and password == 'secret'

@app.route('/')
@auth.login_required
def index():
    return render_template('health_dashboard.html')
```

### Run Behind Nginx Reverse Proxy
Configure Nginx to proxy the dashboard:
```nginx
location /dashboard {
    proxy_pass http://localhost:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Support and Maintenance

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Verify environment configuration
4. Test individual components
5. Consult the repository documentation

## Version History

- **v1.0.0** (2024-01): Initial release
  - Real-time health monitoring
  - REST API endpoints
  - Auto-refresh dashboard
  - Comprehensive statistics
