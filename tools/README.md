# Performance Analyzer Tool

## Overview

The Performance Analyzer is a comprehensive tool for measuring and analyzing the performance of data fetching operations from the Salla API. It provides detailed metrics on response times, throughput, memory usage, and server impact assessment.

## Features

- ✅ **Real-time Performance Measurement** - Measure actual API response times
- ✅ **Throughput Analysis** - Calculate records per second for each endpoint
- ✅ **Memory Profiling** - Track memory consumption during data fetch
- ✅ **Server Impact Assessment** - Analyze potential load on Salla servers
- ✅ **Time Estimation** - Predict total time for full data extraction
- ✅ **Simulation Mode** - Test without making actual API calls
- ✅ **JSON Export** - Save reports for documentation and analysis

## Installation

The tool is already included in the project. Ensure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

Required packages:
- `psutil` - System and process utilities
- `requests` - HTTP library
- `python-dotenv` - Environment variable management

## Usage

### Basic Usage (Simulation Mode)

Run the analyzer without making real API calls:

```bash
python tools/performance_analyzer.py --sample
```

### Live API Testing

Test with actual Salla API (requires valid token):

```bash
python tools/performance_analyzer.py
```

### Custom Record Estimates

Specify estimated record counts for each endpoint:

```bash
python tools/performance_analyzer.py --sample \
  --orders 10000 \
  --customers 5000 \
  --products 2000
```

### Save Report to File

Export the analysis as JSON:

```bash
python tools/performance_analyzer.py --sample --output performance_report.json
```

## Command-Line Options

| Option         | Description                                    | Default |
|----------------|------------------------------------------------|---------|
| `--sample`     | Use simulation mode (no real API calls)        | False   |
| `--orders`     | Estimated number of orders                     | 10000   |
| `--customers`  | Estimated number of customers                  | 5000    |
| `--products`   | Estimated number of products                   | 2000    |
| `--output`     | Output file path for JSON report               | None    |

## Example Output

```
====================================================================================================
DATA FETCH PERFORMANCE ANALYSIS REPORT
====================================================================================================

Generated: 2024-01-15T10:30:00
Mode: SAMPLE
API URL: https://api.salla.dev/admin/v2

----------------------------------------------------------------------------------------------------
OVERALL SUMMARY
----------------------------------------------------------------------------------------------------
Total Estimated Records:  17,000
Total API Requests:       170
Estimated Duration:       240.00 seconds
                          4.00 minutes
                          0.07 hours
Recommended Schedule:     Daily at 2:00 AM UTC during off-peak hours
Expected Completion:      2024-01-15 10:34:00

----------------------------------------------------------------------------------------------------
ENDPOINT PERFORMANCE DETAILS
----------------------------------------------------------------------------------------------------

ORDERS:
  Estimated Records:      10,000
  Estimated Pages:        100
  Duration:               2.33 minutes
  Peak Memory:            75.00 MB
  Avg Throughput:         71.43 records/sec
  API Requests:           100

CUSTOMERS:
  Estimated Records:      5,000
  Estimated Pages:        50
  Duration:               1.17 minutes
  Peak Memory:            37.50 MB
  Avg Throughput:         142.86 records/sec
  API Requests:           50

PRODUCTS:
  Estimated Records:      2,000
  Estimated Pages:        20
  Duration:               0.50 minutes
  Peak Memory:            15.00 MB
  Avg Throughput:         107.14 records/sec
  API Requests:           20

----------------------------------------------------------------------------------------------------
SERVER IMPACT ASSESSMENT
----------------------------------------------------------------------------------------------------
Impact Level:             LOW
Requests per Minute:      ~120
Requests per Hour:        ~7,200
Batch Size:               100
Delay Between Requests:   0.5 seconds

Reasons for Low Impact:
  • Rate limited to ~120 requests/minute
  • Exponential backoff on failures
  • Maximum 3 retries per request
  • 0.5 second delay between requests
  • Batch processing with pagination

Recommendations:
  • Schedule ETL during off-peak hours (e.g., 2-4 AM)
  • Monitor API rate limit headers
  • Implement circuit breaker for API failures
  • Set up alerting for repeated failures
  • Consider incremental loading for large datasets

====================================================================================================
END OF REPORT
====================================================================================================
```

## Report Components

### 1. Overall Summary
- Total estimated records across all endpoints
- Total API requests required
- Estimated duration (seconds, minutes, hours)
- Recommended execution schedule
- Expected completion time

### 2. Endpoint Performance Details
For each endpoint (orders, customers, products):
- Estimated record count
- Number of pages to fetch
- Duration estimate
- Peak memory usage
- Average throughput (records/sec)
- Total API requests

### 3. Server Impact Assessment
- Impact level (LOW/MEDIUM/HIGH)
- Request rate (per minute/hour/day)
- Rate limiting configuration
- Reasons for impact level
- Recommendations for optimization

### 4. System Metrics
- CPU core count
- Total system memory
- Available memory

## Use Cases

### 1. Pre-Production Planning
Run the analyzer before deploying to production to:
- Estimate resource requirements
- Plan execution schedules
- Assess server impact
- Document expected performance

### 2. Performance Monitoring
Use regularly to:
- Track performance trends
- Identify degradation
- Optimize configurations
- Validate SLA compliance

### 3. Documentation
Generate reports for:
- Technical documentation
- Stakeholder communication
- API provider notification (Salla team)
- Capacity planning

### 4. Troubleshooting
When experiencing issues:
- Compare current vs. baseline performance
- Identify bottlenecks
- Validate configuration changes
- Debug slow operations

## Integration with ETL Pipeline

The performance analyzer can be integrated into your ETL pipeline:

```python
from tools.performance_analyzer import PerformanceAnalyzer

# Create analyzer
analyzer = PerformanceAnalyzer(use_sample_mode=False)

# Generate report
report = analyzer.generate_full_report({
    'orders': 10000,
    'customers': 5000,
    'products': 2000
})

# Print to console
analyzer.print_report(report)

# Save to file
import json
with open('performance_report.json', 'w') as f:
    json.dump(report, f, indent=2)
```

## Configuration

The analyzer reads configuration from environment variables:

```bash
# API Configuration
SALLA_API_BASE_URL=https://api.salla.dev/admin/v2
SALLA_API_TOKEN=Bearer your_token_here

# Performance Settings
API_BATCH_SIZE=100
API_MAX_RETRIES=3
API_RETRY_DELAY=5
```

## Metrics Explained

### Response Time
Time taken for a single API request to complete, including:
- Network latency
- Server processing time
- Data transfer time

### Throughput
Number of records processed per second:
```
Throughput = Records Retrieved / Response Time
```

### Memory Usage
Memory consumed during data fetch:
- Start memory: Before request
- End memory: After request
- Memory used: End - Start

### Peak Memory
Estimated maximum memory during full extraction:
```
Peak Memory = Avg Memory per Page × Total Pages × 0.3
```
(Assumes 30% concurrent memory usage)

### Request Rate
Number of API requests over time:
```
Requests/Minute = 60 / Delay Between Requests
```

### Impact Level
Assessment of load on Salla servers:
- **LOW**: <200 req/min, proper delays, off-peak hours
- **MEDIUM**: 200-500 req/min, some delays
- **HIGH**: >500 req/min, aggressive patterns

## Best Practices

1. **Run in Sample Mode First**
   - Test without affecting production API
   - Validate configuration
   - Review report format

2. **Test During Off-Peak Hours**
   - Minimize impact on production
   - Get accurate measurements
   - Avoid rate limiting

3. **Document Results**
   - Save reports for reference
   - Track performance over time
   - Share with stakeholders

4. **Regular Monitoring**
   - Run monthly performance checks
   - Compare against baselines
   - Identify trends early

5. **Configuration Tuning**
   - Adjust batch size based on results
   - Optimize delay between requests
   - Balance speed vs. server impact

## Troubleshooting

### Issue: "API token is required" Error
**Solution:** Set `SALLA_API_TOKEN` in `.env` file or use `--sample` mode

### Issue: Import Error for `psutil`
**Solution:** Install with `pip install psutil`

### Issue: High Memory Usage Reported
**Solution:** This is expected for large datasets. Reduce batch size if needed.

### Issue: Simulation Mode Results Unrealistic
**Solution:** Run with live API for accurate measurements (requires token)

## Contributing

To enhance the performance analyzer:

1. Add new metrics to `measure_single_request()`
2. Extend `analyze_endpoint()` for additional analysis
3. Update `print_report()` for new report sections
4. Add new command-line options as needed

## Related Documentation

- [Data Fetch Performance Report](../docs/DATA_FETCH_PERFORMANCE_REPORT.md)
- [Salla Team Email Template](../docs/SALLA_TEAM_EMAIL_TEMPLATE.md)
- [Architecture Documentation](../docs/ARCHITECTURE.md)
- [Monitoring Guide](../MONITORING_GUIDE.md)

## Support

For issues or questions:
- Check existing documentation
- Review error messages
- Test in simulation mode first
- Contact the data engineering team

## Version History

| Version | Date       | Changes                              |
|---------|------------|--------------------------------------|
| 1.0     | 2024-01-15 | Initial release                      |

---

**Maintained by:** Data Engineering Team  
**Last Updated:** 2024-01-15
