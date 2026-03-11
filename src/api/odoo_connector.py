"""
Odoo API Connector Module

Handles authentication, batch processing, rate limiting, and retry logic
for Odoo ERP REST API integration.

Endpoint pattern:
    GET <base_url>/api/sale/order?order_name=<order_name>

Authentication:
    Bearer token via the Authorization header.
"""

import os
import time
import logging
from typing import Dict, List, Optional
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OdooAPIError(Exception):
    """Custom exception for Odoo API errors"""
    pass


class OdooAPIConnector:
    """
    Connector for the Odoo ERP REST API with built-in retry logic and
    rate-limiting support.
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the Odoo API connector.

        Args:
            api_token: Bearer token for authentication
                       (defaults to ODOO_API_TOKEN env variable)
            base_url: Base URL for the Odoo instance
                      (defaults to ODOO_API_BASE_URL env variable)
        """
        self.api_token = api_token or os.getenv('ODOO_API_TOKEN')
        self.base_url = base_url or os.getenv(
            'ODOO_API_BASE_URL',
            'https://ibrahimalquraishieu-26-2-26-29083802.dev.odoo.com',
        )
        self.max_retries = int(os.getenv('API_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('API_RETRY_DELAY', '5'))

        if not self.api_token:
            raise ValueError(
                "API token is required. Set ODOO_API_TOKEN environment variable."
            )

        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Dict:
        """
        Make an HTTP GET request to the Odoo API with retry logic.

        Args:
            endpoint: API endpoint path (e.g. '/api/sale/order')
            params: Query parameters

        Returns:
            JSON response as a dictionary

        Raises:
            OdooAPIError: If the request fails after all retries
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.info(f"Making request to {url} with params {params}")
            response = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )

            if response.status_code == 429:
                retry_after = int(
                    response.headers.get('Retry-After', self.retry_delay)
                )
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                raise requests.exceptions.RequestException("Rate limited")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def fetch_sale_order(self, order_name: str) -> Dict:
        """
        Fetch a single sale order by its order reference.

        Args:
            order_name: Order reference (e.g. 'S118658')

        Returns:
            API response containing ``order`` and ``order_lines`` keys

        Raises:
            OdooAPIError: If the request fails
        """
        try:
            params = {'order_name': order_name}
            return self._make_request('/api/sale/order', params)
        except Exception as e:
            raise OdooAPIError(
                f"Failed to fetch sale order {order_name}: {str(e)}"
            )

    def fetch_sale_orders(
        self, order_names: List[str], delay: float = 0.5
    ) -> List[Dict]:
        """
        Fetch multiple sale orders by their order references.

        Args:
            order_names: List of order references (e.g. ['S118658', 'S118659'])
            delay: Seconds to wait between requests (rate-limiting)

        Returns:
            List of API responses, one per order
        """
        results: List[Dict] = []

        for order_name in order_names:
            try:
                logger.info(f"Fetching Odoo sale order: {order_name}")
                response = self.fetch_sale_order(order_name)
                results.append(response)
                time.sleep(delay)
            except OdooAPIError as e:
                logger.error(f"Skipping order {order_name}: {str(e)}")

        logger.info(f"Fetched {len(results)} Odoo sale orders")
        return results

    def extract_order(self, response: Dict) -> Optional[Dict]:
        """
        Extract the order record from an API response.

        Args:
            response: API response dictionary

        Returns:
            Order dictionary or None if not present
        """
        return response.get('order')

    def extract_order_lines(self, response: Dict) -> List[Dict]:
        """
        Extract order line records from an API response.

        Args:
            response: API response dictionary

        Returns:
            List of order line dictionaries
        """
        return response.get('order_lines', [])


if __name__ == "__main__":
    try:
        connector = OdooAPIConnector()
        response = connector.fetch_sale_order('S118658')
        order = connector.extract_order(response)
        lines = connector.extract_order_lines(response)
        print(f"Order: {order.get('order_name')} | Lines: {len(lines)}")
    except Exception as exc:
        print(f"Error: {exc}")
