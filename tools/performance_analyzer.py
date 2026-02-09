"""
Data Fetch Performance Analyzer

Measures and analyzes the performance of data fetching from Salla API including:
- API response times
- Throughput (records per second)
- Total data fetch time estimates
- Memory and resource usage
- Pagination performance
- Server impact assessment
"""

import os
import sys
import time
import logging
import psutil
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import requests

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.api.salla_connector import SallaAPIConnector, SallaAPIError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Analyzes performance of data fetching operations."""
    
    def __init__(self, use_sample_mode: bool = False):
        """
        Initialize the performance analyzer.
        
        Args:
            use_sample_mode: If True, simulates API calls instead of making real ones
        """
        self.use_sample_mode = use_sample_mode
        self.api_connector = None
        
        if not use_sample_mode:
            try:
                self.api_connector = SallaAPIConnector()
            except ValueError as e:
                logger.warning(f"API connector initialization failed: {e}")
                logger.warning("Running in sample/simulation mode")
                self.use_sample_mode = True
        
        self.metrics = {
            'orders': {},
            'customers': {},
            'products': {}
        }
    
    def measure_single_request(self, endpoint: str, page: int = 1) -> Dict[str, Any]:
        """
        Measure performance of a single API request.
        
        Args:
            endpoint: API endpoint ('orders', 'customers', or 'products')
            page: Page number to fetch
            
        Returns:
            Dictionary with performance metrics
        """
        if self.use_sample_mode:
            return self._simulate_request(endpoint, page)
        
        try:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Fetch data based on endpoint
            if endpoint == 'orders':
                response = self.api_connector.fetch_orders(page=page)
            elif endpoint == 'customers':
                response = self.api_connector.fetch_customers(page=page)
            elif endpoint == 'products':
                response = self.api_connector.fetch_products(page=page)
            else:
                raise ValueError(f"Invalid endpoint: {endpoint}")
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_used = end_memory - start_memory
            
            data = response.get('data', [])
            record_count = len(data)
            
            # Calculate throughput
            throughput = record_count / duration if duration > 0 else 0
            
            return {
                'success': True,
                'endpoint': endpoint,
                'page': page,
                'duration_seconds': round(duration, 3),
                'record_count': record_count,
                'throughput_records_per_sec': round(throughput, 2),
                'memory_mb': round(memory_used, 2),
                'timestamp': datetime.now().isoformat(),
                'response_size_kb': len(str(response)) / 1024 if response else 0
            }
            
        except Exception as e:
            logger.error(f"Error measuring {endpoint} request: {str(e)}")
            return {
                'success': False,
                'endpoint': endpoint,
                'page': page,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _simulate_request(self, endpoint: str, page: int = 1) -> Dict[str, Any]:
        """Simulate API request for testing without actual API calls."""
        # Simulate realistic delays and data sizes
        time.sleep(0.5 + (page * 0.1))  # Simulate network latency
        
        record_counts = {
            'orders': 50,
            'customers': 100,
            'products': 75
        }
        
        return {
            'success': True,
            'endpoint': endpoint,
            'page': page,
            'duration_seconds': round(0.5 + (page * 0.1), 3),
            'record_count': record_counts.get(endpoint, 50),
            'throughput_records_per_sec': round(record_counts.get(endpoint, 50) / (0.5 + (page * 0.1)), 2),
            'memory_mb': round(2.5 + (page * 0.5), 2),
            'timestamp': datetime.now().isoformat(),
            'response_size_kb': round(15.5 + (page * 2.3), 2),
            'simulated': True
        }
    
    def analyze_endpoint(self, endpoint: str, num_pages: int = 5) -> Dict[str, Any]:
        """
        Analyze performance for a specific endpoint across multiple pages.
        
        Args:
            endpoint: API endpoint to analyze
            num_pages: Number of pages to test
            
        Returns:
            Aggregated performance metrics
        """
        logger.info(f"Analyzing {endpoint} endpoint ({num_pages} pages)...")
        
        measurements = []
        total_records = 0
        total_duration = 0
        
        for page in range(1, num_pages + 1):
            logger.info(f"  Measuring page {page}/{num_pages}...")
            result = self.measure_single_request(endpoint, page)
            
            if result['success']:
                measurements.append(result)
                total_records += result['record_count']
                total_duration += result['duration_seconds']
            else:
                logger.warning(f"  Failed to measure page {page}: {result.get('error')}")
        
        if not measurements:
            return {
                'endpoint': endpoint,
                'success': False,
                'error': 'No successful measurements'
            }
        
        # Calculate statistics
        durations = [m['duration_seconds'] for m in measurements]
        throughputs = [m['throughput_records_per_sec'] for m in measurements]
        memory_usage = [m['memory_mb'] for m in measurements]
        
        return {
            'endpoint': endpoint,
            'success': True,
            'pages_analyzed': len(measurements),
            'total_records': total_records,
            'total_duration_seconds': round(total_duration, 2),
            'avg_duration_per_page': round(statistics.mean(durations), 3),
            'min_duration': round(min(durations), 3),
            'max_duration': round(max(durations), 3),
            'avg_throughput': round(statistics.mean(throughputs), 2),
            'min_throughput': round(min(throughputs), 2),
            'max_throughput': round(max(throughputs), 2),
            'avg_memory_mb': round(statistics.mean(memory_usage), 2),
            'total_memory_mb': round(sum(memory_usage), 2),
            'measurements': measurements
        }
    
    def estimate_full_data_fetch(self, endpoint: str, estimated_total_records: int,
                                 records_per_page: int = 100) -> Dict[str, Any]:
        """
        Estimate time and resources for fetching all data from an endpoint.
        
        Args:
            endpoint: API endpoint
            estimated_total_records: Estimated total number of records
            records_per_page: Number of records per page
            
        Returns:
            Estimation metrics
        """
        # Get sample performance data
        sample_result = self.analyze_endpoint(endpoint, num_pages=3)
        
        if not sample_result['success']:
            return {
                'endpoint': endpoint,
                'success': False,
                'error': 'Failed to get sample data'
            }
        
        # Calculate estimates
        total_pages = (estimated_total_records + records_per_page - 1) // records_per_page
        avg_duration_per_page = sample_result['avg_duration_per_page']
        avg_memory_per_page = sample_result['avg_memory_mb']
        
        estimated_total_duration = total_pages * avg_duration_per_page
        estimated_peak_memory = total_pages * avg_memory_per_page * 0.3  # Estimate 30% concurrent
        
        # Add delays between requests (0.5 seconds per page for rate limiting)
        rate_limit_delay = total_pages * 0.5
        total_time_with_delays = estimated_total_duration + rate_limit_delay
        
        return {
            'endpoint': endpoint,
            'success': True,
            'estimated_total_records': estimated_total_records,
            'estimated_total_pages': total_pages,
            'records_per_page': records_per_page,
            'estimated_duration_seconds': round(total_time_with_delays, 2),
            'estimated_duration_minutes': round(total_time_with_delays / 60, 2),
            'estimated_duration_hours': round(total_time_with_delays / 3600, 2),
            'estimated_peak_memory_mb': round(estimated_peak_memory, 2),
            'avg_throughput': sample_result['avg_throughput'],
            'rate_limit_delay_seconds': rate_limit_delay,
            'api_requests_count': total_pages
        }
    
    def analyze_server_impact(self) -> Dict[str, Any]:
        """
        Analyze potential impact on Salla server.
        
        Returns:
            Server impact assessment
        """
        # Get rate limiting configuration
        batch_size = int(os.getenv('API_BATCH_SIZE', '100'))
        retry_delay = int(os.getenv('API_RETRY_DELAY', '5'))
        max_retries = int(os.getenv('API_MAX_RETRIES', '3'))
        
        # Calculate request rate
        requests_per_minute = 60 / 0.5  # With 0.5 second delay between requests
        requests_per_hour = requests_per_minute * 60
        requests_per_day = requests_per_hour * 24
        
        return {
            'rate_limiting': {
                'batch_size': batch_size,
                'delay_between_requests': 0.5,
                'retry_delay_seconds': retry_delay,
                'max_retries': max_retries
            },
            'request_rate': {
                'requests_per_minute': round(requests_per_minute, 2),
                'requests_per_hour': round(requests_per_hour, 2),
                'requests_per_day': round(requests_per_day, 2)
            },
            'server_impact_assessment': {
                'impact_level': 'LOW',
                'reasons': [
                    f'Rate limited to ~{int(requests_per_minute)} requests/minute',
                    'Exponential backoff on failures',
                    f'Maximum {max_retries} retries per request',
                    '0.5 second delay between requests',
                    'Batch processing with pagination'
                ],
                'recommendations': [
                    'Schedule ETL during off-peak hours (e.g., 2-4 AM)',
                    'Monitor API rate limit headers',
                    'Implement circuit breaker for API failures',
                    'Set up alerting for repeated failures',
                    'Consider incremental loading for large datasets'
                ]
            },
            'data_transfer': {
                'daily_schedule': '2:00 AM UTC',
                'expected_duration': '15-30 minutes for typical datasets',
                'peak_concurrent_connections': 1,
                'connection_persistence': 'Keep-alive enabled'
            }
        }
    
    def generate_full_report(self, estimated_records: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            estimated_records: Dictionary with estimated record counts per endpoint
            
        Returns:
            Complete performance report
        """
        if estimated_records is None:
            estimated_records = {
                'orders': 10000,
                'customers': 5000,
                'products': 2000
            }
        
        logger.info("Generating comprehensive performance report...")
        logger.info("=" * 80)
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'mode': 'SAMPLE' if self.use_sample_mode else 'LIVE API',
                'api_base_url': os.getenv('SALLA_API_BASE_URL', 'https://api.salla.dev/admin/v2')
            },
            'endpoint_analysis': {},
            'full_data_fetch_estimates': {},
            'server_impact': self.analyze_server_impact(),
            'system_metrics': {
                'cpu_count': psutil.cpu_count(),
                'total_memory_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                'available_memory_gb': round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2)
            }
        }
        
        # Analyze each endpoint
        total_estimated_time = 0
        for endpoint, record_count in estimated_records.items():
            # Get detailed analysis
            logger.info(f"\nAnalyzing {endpoint.upper()}...")
            analysis = self.analyze_endpoint(endpoint, num_pages=3)
            report['endpoint_analysis'][endpoint] = analysis
            
            # Get full fetch estimate
            if analysis['success']:
                estimate = self.estimate_full_data_fetch(endpoint, record_count)
                report['full_data_fetch_estimates'][endpoint] = estimate
                total_estimated_time += estimate['estimated_duration_seconds']
        
        # Add overall summary
        report['overall_summary'] = {
            'total_estimated_duration_seconds': round(total_estimated_time, 2),
            'total_estimated_duration_minutes': round(total_estimated_time / 60, 2),
            'total_estimated_duration_hours': round(total_estimated_time / 3600, 2),
            'total_estimated_records': sum(estimated_records.values()),
            'total_api_requests': sum(
                report['full_data_fetch_estimates'].get(e, {}).get('api_requests_count', 0)
                for e in estimated_records.keys()
            ),
            'recommended_schedule': 'Daily at 2:00 AM UTC during off-peak hours',
            'expected_completion_time': (
                datetime.now() + timedelta(seconds=total_estimated_time)
            ).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info("=" * 80)
        logger.info("Report generation complete!")
        
        return report
    
    def print_report(self, report: Dict[str, Any]) -> None:
        """Print formatted performance report."""
        print("\n" + "=" * 100)
        print("DATA FETCH PERFORMANCE ANALYSIS REPORT")
        print("=" * 100)
        print(f"\nGenerated: {report['report_metadata']['generated_at']}")
        print(f"Mode: {report['report_metadata']['mode']}")
        print(f"API URL: {report['report_metadata']['api_base_url']}")
        
        print("\n" + "-" * 100)
        print("OVERALL SUMMARY")
        print("-" * 100)
        summary = report['overall_summary']
        print(f"Total Estimated Records:  {summary['total_estimated_records']:,}")
        print(f"Total API Requests:       {summary['total_api_requests']:,}")
        print(f"Estimated Duration:       {summary['total_estimated_duration_seconds']:.2f} seconds")
        print(f"                          {summary['total_estimated_duration_minutes']:.2f} minutes")
        print(f"                          {summary['total_estimated_duration_hours']:.2f} hours")
        print(f"Recommended Schedule:     {summary['recommended_schedule']}")
        print(f"Expected Completion:      {summary['expected_completion_time']}")
        
        print("\n" + "-" * 100)
        print("ENDPOINT PERFORMANCE DETAILS")
        print("-" * 100)
        
        for endpoint, estimate in report['full_data_fetch_estimates'].items():
            print(f"\n{endpoint.upper()}:")
            print(f"  Estimated Records:      {estimate['estimated_total_records']:,}")
            print(f"  Estimated Pages:        {estimate['estimated_total_pages']:,}")
            print(f"  Duration:               {estimate['estimated_duration_minutes']:.2f} minutes")
            print(f"  Peak Memory:            {estimate['estimated_peak_memory_mb']:.2f} MB")
            print(f"  Avg Throughput:         {estimate['avg_throughput']:.2f} records/sec")
            print(f"  API Requests:           {estimate['api_requests_count']:,}")
        
        print("\n" + "-" * 100)
        print("SERVER IMPACT ASSESSMENT")
        print("-" * 100)
        impact = report['server_impact']
        print(f"Impact Level:             {impact['server_impact_assessment']['impact_level']}")
        print(f"Requests per Minute:      ~{impact['request_rate']['requests_per_minute']:.0f}")
        print(f"Requests per Hour:        ~{impact['request_rate']['requests_per_hour']:.0f}")
        print(f"Batch Size:               {impact['rate_limiting']['batch_size']}")
        print(f"Delay Between Requests:   {impact['rate_limiting']['delay_between_requests']} seconds")
        
        print("\nReasons for Low Impact:")
        for reason in impact['server_impact_assessment']['reasons']:
            print(f"  • {reason}")
        
        print("\nRecommendations:")
        for rec in impact['server_impact_assessment']['recommendations']:
            print(f"  • {rec}")
        
        print("\n" + "-" * 100)
        print("SYSTEM RESOURCES")
        print("-" * 100)
        sys_metrics = report['system_metrics']
        print(f"CPU Cores:                {sys_metrics['cpu_count']}")
        print(f"Total Memory:             {sys_metrics['total_memory_gb']:.2f} GB")
        print(f"Available Memory:         {sys_metrics['available_memory_gb']:.2f} GB")
        
        print("\n" + "=" * 100)
        print("END OF REPORT")
        print("=" * 100 + "\n")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Salla API data fetch performance')
    parser.add_argument('--sample', action='store_true',
                       help='Use sample/simulation mode (no real API calls)')
    parser.add_argument('--orders', type=int, default=10000,
                       help='Estimated number of orders (default: 10000)')
    parser.add_argument('--customers', type=int, default=5000,
                       help='Estimated number of customers (default: 5000)')
    parser.add_argument('--products', type=int, default=2000,
                       help='Estimated number of products (default: 2000)')
    parser.add_argument('--output', type=str,
                       help='Output file path for JSON report')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = PerformanceAnalyzer(use_sample_mode=args.sample)
    
    # Generate report
    estimated_records = {
        'orders': args.orders,
        'customers': args.customers,
        'products': args.products
    }
    
    report = analyzer.generate_full_report(estimated_records)
    
    # Print report
    analyzer.print_report(report)
    
    # Save to file if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Report saved to: {args.output}")


if __name__ == '__main__':
    main()
