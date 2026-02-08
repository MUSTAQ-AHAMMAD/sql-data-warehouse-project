# API Testing Dashboard

## Overview
The API Testing Dashboard is a modern web interface for testing API endpoints, monitoring data quality, and tracking errors in the ETL pipeline.

## Features

### 1. Real-Time Statistics
- Total data sources count
- Error tracking
- DLQ record count
- System health status

### 2. Data Source Management
- View all configured data sources
- Enable/disable sources
- Test connections
- View supported entities

### 3. API Testing
- Select data source and entity type
- Fetch data with pagination
- View JSON responses
- Copy responses to clipboard

### 4. Data Validation
- Schema validation
- Quality checks
- Data profiling
- Type verification

### 5. Quality Metrics
- Row and column counts
- Null value percentages
- Duplicate detection
- Statistical summaries

### 6. Error Tracking
- Error summary by severity
- Error categorization
- Recent error history
- DLQ file management

## Quick Start

### Start the Dashboard
```bash
python start_dashboard.py --port 5000
```

### Options
```bash
python start_dashboard.py --help

Options:
  --port PORT      Port to run on (default: 5000)
  --host HOST      Host to bind to (default: 0.0.0.0)
  --debug          Enable debug mode
```

### Access
Open your browser and navigate to:
```
http://localhost:5000
```

## API Endpoints

### Health Check
```bash
GET /api/health
```
Returns system health status.

### List Data Sources
```bash
GET /api/sources
```
Returns all configured data sources.

### Test Connection
```bash
GET /api/sources/{source_name}/test
```
Tests connection to a specific data source.

### Fetch Data
```bash
GET /api/sources/{source_name}/entities/{entity_type}/fetch?page=1&per_page=10
```
Fetches data from a specific source and entity.

### Validate Schema
```bash
POST /api/validate/schema
Content-Type: application/json

{
  "records": [...],
  "entity_type": "orders"
}
```
Validates data against schema.

### Validate Quality
```bash
POST /api/validate/quality
Content-Type: application/json

{
  "records": [...]
}
```
Validates data quality.

### Get Error Summary
```bash
GET /api/errors/summary
```
Returns error summary statistics.

### List DLQ Files
```bash
GET /api/dlq/files?source=salla&entity_type=orders
```
Lists Dead Letter Queue files.

### Get Statistics
```bash
GET /api/stats
```
Returns dashboard statistics.

## Configuration

### Environment Variables
Set in `.env` file:

```bash
# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
DASHBOARD_DEBUG=False

# Data Quality
DLQ_DIRECTORY=./data/dlq
ENABLE_DATA_VALIDATION=True
```

### Data Sources
Configure in `config/data_sources.yaml`:

```yaml
data_sources:
  salla:
    enabled: true
    api_token: ${SALLA_API_TOKEN}
    base_url: ${SALLA_API_BASE_URL}
    batch_size: 100
    max_retries: 3
    retry_delay: 5
    supported_entities:
      - orders
      - customers
      - products
```

## Usage Examples

### Testing an API Endpoint

1. Open dashboard in browser
2. Select "Salla" from Data Source dropdown
3. Select "Orders" from Entity Type dropdown
4. Set page number and per page count
5. Click "Fetch Data"
6. View the JSON response

### Validating Data

1. Fetch data using the steps above
2. Click "Validate" button
3. View validation results:
   - Schema validation status
   - Quality check results
   - Data profile statistics

### Monitoring Errors

1. Check the "Error Tracking" panel
2. View total errors by severity
3. Check Dead Letter Queue for failed records
4. Click on error details for more information

### Testing Connection

1. Click on a data source in the left panel
2. Dashboard will test the connection
3. Toast notification shows result
4. Connection status updates

## Dashboard Components

### Header
- Dashboard title
- Real-time refresh button
- System status indicator

### Statistics Cards
- Data Sources count
- Total Errors count
- DLQ Records count
- System Status

### Data Sources Panel
- List of all configured sources
- Enable/disable status
- Click to test connection
- Shows description

### API Testing Panel
- Source and entity selection
- Pagination controls
- Fetch and validate buttons
- Response display area
- Validation results

### Error Tracking Panel
- Error summary statistics
- Error breakdown by severity
- Dead Letter Queue list
- Recent error history

### Data Quality Metrics Panel
- Row and column counts
- Null value analysis
- Quality score
- Statistical summaries

## Keyboard Shortcuts

- `Ctrl/Cmd + R` - Refresh dashboard
- `Ctrl/Cmd + C` - Copy API response (when in focus)

## Troubleshooting

### Dashboard Won't Start

**Issue**: Port already in use
```bash
# Solution: Use a different port
python start_dashboard.py --port 5001
```

**Issue**: Missing dependencies
```bash
# Solution: Install requirements
pip install Flask Flask-CORS PyYAML
```

### API Endpoints Return Errors

**Issue**: Invalid API token
```bash
# Solution: Check .env file
# Ensure SALLA_API_TOKEN is set correctly
```

**Issue**: Connection timeout
```bash
# Solution: Check network connectivity
# Verify base URL is correct
```

### Validation Fails

**Issue**: Schema mismatch
```bash
# Solution: Check config/data_sources.yaml
# Verify schema definitions match API response
```

**Issue**: Data type errors
```bash
# Solution: Review data types in config
# Ensure compatibility with API data
```

### Dashboard UI Not Updating

**Issue**: JavaScript errors
```bash
# Solution: Check browser console
# Clear browser cache
# Refresh page (F5)
```

**Issue**: API not responding
```bash
# Solution: Check backend logs
# Restart dashboard
# Verify API endpoints are accessible
```

## Performance Tips

1. **Pagination**: Use appropriate per_page values (10-100)
2. **Caching**: Dashboard caches data source information
3. **Refresh**: Use refresh button instead of page reload
4. **Batch Size**: Configure in data_sources.yaml for optimal performance

## Security Considerations

1. **Authentication**: Dashboard runs on localhost by default
2. **API Tokens**: Store in .env file, never commit
3. **CORS**: Configured for localhost only
4. **Production**: Use WSGI server (gunicorn) for production
5. **HTTPS**: Enable SSL/TLS for production deployments

## Production Deployment

### Using Gunicorn (Recommended)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 dashboard.app:app
```

### Using uWSGI

```bash
pip install uwsgi

uwsgi --http :5000 --wsgi-file dashboard/app.py --callable app
```

### Using Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "dashboard.app:app"]
```

## Development

### Project Structure
```
dashboard/
├── app.py              # Flask application
├── templates/
│   └── index.html      # Dashboard UI
└── static/
    ├── css/
    │   └── style.css   # Styling
    └── js/
        └── api_tester.js  # Frontend logic
```

### Adding New Features

1. **Backend**: Add endpoint to `dashboard/app.py`
2. **Frontend**: Update `static/js/api_tester.js`
3. **UI**: Modify `templates/index.html`
4. **Styling**: Update `static/css/style.css`

### Testing

```bash
# Test API endpoints
curl http://localhost:5000/api/health

# Test with specific parameters
curl http://localhost:5000/api/sources
```

## Support

For issues or questions:
1. Check browser console for JavaScript errors
2. Check backend logs for Python errors
3. Review configuration files
4. Verify environment variables
5. Check network connectivity

## License

This dashboard is part of the SQL Data Warehouse ETL Pipeline project and follows the same MIT License.
