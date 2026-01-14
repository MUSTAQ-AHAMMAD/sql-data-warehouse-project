"""
Salla API Connector Module

Handles authentication, batch processing, rate limiting, and retry logic for Salla API integration.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SallaAPIError(Exception):
    """Custom exception for Salla API errors"""
    pass


class SallaAPIConnector:
    """
    Connector for Salla API with built-in batch processing, retry logic, and rate limiting.
    """
    
    def __init__(self, api_token: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Salla API connector.
        
        Args:
            api_token: Bearer token for authentication (defaults to env variable)
            base_url: Base URL for Salla API (defaults to env variable)
        """
        self.api_token = api_token or os.getenv('SALLA_API_TOKEN')
        self.base_url = base_url or os.getenv('SALLA_API_BASE_URL', 'https://api.salla.dev/admin/v2')
        self.batch_size = int(os.getenv('API_BATCH_SIZE', '100'))
        self.max_retries = int(os.getenv('API_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('API_RETRY_DELAY', '5'))
        
        if not self.api_token:
            raise ValueError("API token is required. Set SALLA_API_TOKEN environment variable.")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to Salla API with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., '/orders')
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            SallaAPIError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Making request to {url} with params {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                raise requests.exceptions.RequestException("Rate limited")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def fetch_orders(self, page: int = 1, per_page: Optional[int] = None) -> Dict:
        """
        Fetch orders from Salla API.
        
        Args:
            page: Page number
            per_page: Number of items per page (defaults to batch_size)
            
        Returns:
            API response containing orders
        """
        per_page = per_page or self.batch_size
        params = {'page': page, 'per_page': per_page}
        return self._make_request('/orders', params)
    
    def fetch_customers(self, page: int = 1, per_page: Optional[int] = None) -> Dict:
        """
        Fetch customers from Salla API.
        
        Args:
            page: Page number
            per_page: Number of items per page (defaults to batch_size)
            
        Returns:
            API response containing customers
        """
        per_page = per_page or self.batch_size
        params = {'page': page, 'per_page': per_page}
        return self._make_request('/customers', params)
    
    def fetch_products(self, page: int = 1, per_page: Optional[int] = None) -> Dict:
        """
        Fetch products from Salla API.
        
        Args:
            page: Page number
            per_page: Number of items per page (defaults to batch_size)
            
        Returns:
            API response containing products
        """
        per_page = per_page or self.batch_size
        params = {'page': page, 'per_page': per_page}
        return self._make_request('/products', params)
    
    def fetch_all_pages(self, endpoint_method: str, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Fetch all pages of data from a specific endpoint with batch processing.
        
        Args:
            endpoint_method: Method name ('orders', 'customers', or 'products')
            max_pages: Maximum number of pages to fetch (None for all)
            
        Returns:
            List of all records from all pages
        """
        all_records = []
        page = 1
        
        method_map = {
            'orders': self.fetch_orders,
            'customers': self.fetch_customers,
            'products': self.fetch_products
        }
        
        if endpoint_method not in method_map:
            raise ValueError(f"Invalid endpoint method: {endpoint_method}")
        
        fetch_method = method_map[endpoint_method]
        
        while True:
            if max_pages and page > max_pages:
                break
                
            try:
                logger.info(f"Fetching {endpoint_method} page {page}")
                response = fetch_method(page=page)
                
                # Handle different response structures with validation
                data = response.get('data', [])
                if not data:
                    logger.warning(f"No data returned for {endpoint_method} page {page}")
                    break
                
                all_records.extend(data)
                
                # Check pagination info (handle missing pagination gracefully)
                pagination = response.get('pagination', {})
                if not pagination:
                    logger.info(f"No pagination info, assuming last page for {endpoint_method}")
                    break
                    
                if not pagination.get('hasMorePages', False):
                    break
                
                page += 1
                
                # Rate limiting delay between pages
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {str(e)}")
                raise SallaAPIError(f"Failed to fetch {endpoint_method}: {str(e)}")
        
        logger.info(f"Fetched total of {len(all_records)} {endpoint_method}")
        return all_records


if __name__ == "__main__":
    # Example usage
    try:
        connector = SallaAPIConnector()
        
        # Test fetching first page of orders
        orders = connector.fetch_orders(page=1)
        print(f"Fetched {len(orders.get('data', []))} orders")
        
    except Exception as e:
        print(f"Error: {str(e)}")
