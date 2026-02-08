# Enhanced Scalability Architecture & API Testing Dashboard

## Overview

This enhancement adds a scalable, plugin-based architecture to the ETL pipeline with comprehensive API testing and data quality monitoring capabilities.

## New Features

### 1. Generic API Adapter Interface

**File**: `src/api/generic_api_adapter.py`

A flexible, plugin-based architecture for integrating multiple data sources:

- **Abstract base class** for all API adapters
- **Automatic pagination** and batch processing
- **Built-in retry logic** with exponential backoff
- **Rate limiting** support
- **Schema validation** capabilities
- **Connection testing** functionality

**Usage Example**:
```python
from src.api.salla_adapter import SallaAPIAdapter

config = {
    'api_token': 'your_token',
    'base_url': 'https://api.salla.dev/admin/v2',
    'batch_size': 100,
    'source_name': 'salla'
}

adapter = SallaAPIAdapter(config)
orders = adapter.fetch_all_pages('orders', max_pages=5)
```

### 2. Data Source Registry

**File**: `src/api/data_source_registry.py`

Centralized management of multiple data sources:

- **Config-driven** source registration
- **Environment variable** resolution
- **Connection testing** for all sources
- **Configuration validation**
- **Adapter caching** for performance

**Usage Example**:
```python
from src.api.data_source_registry import get_registry

registry = get_registry()
adapter = registry.get_adapter('salla')
data = adapter.fetch_data('orders', page=1)
```

### 3. Data Validation Framework

**File**: `src/utils/data_validator.py`

Comprehensive data quality validation:

- **Schema validation** (field types, required fields)
- **Data quality checks** (duplicates, null values)
- **Data profiling** (statistics, metrics)
- **Schema comparison** tools
- **Great Expectations** integration (optional)

**Usage Example**:
```python
from src.utils.data_validator import DataValidator
import pandas as pd

validator = DataValidator()
df = pd.DataFrame(your_data)

# Validate schema
schema = {'required_fields': ['id', 'name'], ...}
result = validator.validate_schema(df, schema)

# Get data profile
profile = validator.get_data_profile(df)
```

### 4. Error Handler with DLQ

**File**: `src/utils/error_handler.py`

Centralized error handling and failed record management:

- **Error classification** by severity and category
- **Dead Letter Queue** (DLQ) for failed records
- **Automatic retry** mechanisms
- **Error tracking** and reporting
- **Batch processing** with error handling

**Usage Example**:
```python
from src.utils.error_handler import ErrorHandler, ErrorSeverity

handler = ErrorHandler()

# Handle error
error_record = handler.handle_error(
    exception,
    context={'operation': 'data_fetch'},
    severity=ErrorSeverity.HIGH
)

# Send to DLQ
handler.send_to_dlq(failed_record, exception, 'salla', 'orders')

# Retry failed records
handler.retry_dlq_records(process_function, source='salla')
```

### 5. API Testing Dashboard

**Files**: 
- `dashboard/app.py` - Flask backend
- `dashboard/templates/index.html` - Web UI
- `dashboard/static/css/style.css` - Styling
- `dashboard/static/js/api_tester.js` - Frontend logic

A modern web interface for:

- **API endpoint testing** with real-time responses
- **Data validation** at each layer
- **Quality metrics** visualization
- **Error tracking** and DLQ monitoring
- **Schema comparison** tools
- **Connection testing** for all sources

**Starting the Dashboard**:
```bash
python start_dashboard.py --port 5000
```

Then access: `http://localhost:5000`

## Configuration

### Data Sources Configuration

**File**: `config/data_sources.yaml`

Configure multiple data sources:

```yaml
data_sources:
  salla:
    enabled: true
    api_token: ${SALLA_API_TOKEN}
    base_url: ${SALLA_API_BASE_URL}
    batch_size: 100
    max_retries: 3
    supported_entities:
      - orders
      - customers
      - products
```

### Environment Variables

Add to `.env`:

```bash
# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
DASHBOARD_DEBUG=False

# Data Quality
DLQ_DIRECTORY=./data/dlq
ENABLE_DATA_VALIDATION=True
```

## Adding New Data Sources

### Step 1: Create Adapter Class

```python
from src.api.generic_api_adapter import GenericAPIAdapter

class MyAPIAdapter(GenericAPIAdapter):
    def _setup_headers(self):
        return {'Authorization': f'Bearer {self.api_token}'}
    
    def get_schema(self, entity_type):
        # Define schema for entity
        return {...}
    
    def fetch_data(self, entity_type, page=1, per_page=None):
        # Implement data fetching
        return self._make_request(f'/{entity_type}', params={'page': page})
    
    def _extract_data_from_response(self, response):
        return response.get('data', [])
    
    def _has_more_pages(self, response):
        return response.get('has_more', False)
    
    def get_supported_entities(self):
        return ['entity1', 'entity2']
```

### Step 2: Register Adapter

```python
from src.api.data_source_registry import get_registry

registry = get_registry()
registry.register_adapter('my_api', MyAPIAdapter)
```

### Step 3: Add Configuration

Update `config/data_sources.yaml`:

```yaml
data_sources:
  my_api:
    enabled: true
    api_token: ${MY_API_TOKEN}
    base_url: ${MY_API_BASE_URL}
    batch_size: 100
```

## Dashboard Features

### 1. API Testing
- Select data source and entity type
- Fetch data with pagination
- View JSON responses
- Real-time error handling

### 2. Data Validation
- Schema validation
- Quality checks
- Field-level profiling
- Type compatibility checks

### 3. Quality Metrics
- Row/column counts
- Null value percentages
- Duplicate detection
- Data type distribution

### 4. Error Tracking
- Error summary by severity
- Error categorization
- Recent error history
- DLQ file management

### 5. DLQ Management
- View failed records
- Filter by source/entity
- Retry processing
- Export error logs

## Testing

Run the component tests:

```bash
python tests/test_architecture.py
```

Test individual components:

```python
# Test data source registry
from src.api.data_source_registry import get_registry
registry = get_registry()
print(registry.list_sources())

# Test validator
from src.utils.data_validator import DataValidator
validator = DataValidator()
profile = validator.get_data_profile(df)

# Test error handler
from src.utils.error_handler import ErrorHandler
handler = ErrorHandler()
summary = handler.get_error_summary()
```

## Architecture Benefits

1. **Scalability**: Easy to add new data sources without code duplication
2. **Maintainability**: Centralized error handling and validation
3. **Observability**: Real-time monitoring through dashboard
4. **Reliability**: DLQ ensures no data loss
5. **Flexibility**: Config-driven architecture
6. **Testability**: Isolated components with clear interfaces

## Dependencies

New dependencies added to `requirements.txt`:

```
Flask==3.0.0
Flask-CORS==4.0.0
great-expectations==0.18.8
plotly==5.18.0
PyYAML==6.0.1
```

Install with:
```bash
pip install -r requirements.txt
```

## Best Practices

### 1. Error Handling
- Always use the error handler for consistent logging
- Send failed records to DLQ for retry
- Monitor error trends in the dashboard

### 2. Data Validation
- Validate data at each layer (Bronze, Silver, Gold)
- Use schema validation before transformations
- Profile data to detect anomalies

### 3. API Integration
- Use adapters for all external APIs
- Configure retry logic appropriately
- Monitor rate limits through dashboard

### 4. Configuration Management
- Use environment variables for sensitive data
- Keep schemas in config files
- Version control configuration changes

## Troubleshooting

### Dashboard Won't Start
```bash
# Check dependencies
pip install Flask Flask-CORS PyYAML

# Check port availability
lsof -i :5000

# Run with debug mode
python start_dashboard.py --debug
```

### Validation Errors
```bash
# Check schema configuration
cat config/data_sources.yaml

# Verify data format
python -c "from src.utils.data_validator import DataValidator; ..."
```

### DLQ Files Accumulating
```bash
# List DLQ files
ls -l data/dlq/

# Retry failed records
from src.utils.error_handler import ErrorHandler
handler = ErrorHandler()
handler.retry_dlq_records(process_func)
```

## Future Enhancements

- Real-time data streaming support
- Machine learning-based anomaly detection
- Advanced visualization with Plotly dashboards
- Automated testing for transformations
- Performance profiling and optimization
- Multi-user authentication for dashboard
- Webhook support for error notifications
- Data lineage tracking

## Support

For issues or questions:
1. Check the dashboard health endpoint: `http://localhost:5000/api/health`
2. Review error logs in the dashboard
3. Check DLQ files for failed records
4. Run component tests to verify setup
