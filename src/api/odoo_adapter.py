"""
Odoo API Adapter

Concrete implementation of GenericAPIAdapter for Odoo ERP API.
Handles sale orders and order lines from the Odoo REST API.
"""

import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from .generic_api_adapter import GenericAPIAdapter, APIAdapterError

load_dotenv()


class OdooAPIAdapter(GenericAPIAdapter):
    """
    Odoo API adapter implementing the GenericAPIAdapter interface.
    Provides integration with the Odoo ERP platform REST API.

    The Odoo API returns individual sale orders keyed by order_name:
        GET /api/sale/order?order_name=<order_name>
    Response structure:
        {
            "order": { ... },
            "order_lines": [ ... ]
        }
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Odoo API adapter.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

    def _setup_headers(self) -> Dict[str, str]:
        """
        Setup HTTP headers for Odoo API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def get_schema(self, entity_type: str) -> Dict[str, Any]:
        """
        Get the schema definition for an Odoo entity type.

        Args:
            entity_type: Type of entity (sales_orders, sales_order_lines)

        Returns:
            Schema definition dictionary
        """
        schemas = {
            'sales_orders': {
                'required_fields': [
                    'order_id', 'order_name', 'date_order',
                    'customer_id', 'order_amount_total', 'order_state',
                ],
                'field_types': {
                    'order_id': 'int',
                    'order_name': 'string',
                    'date_order': 'datetime',
                    'customer_id': 'int',
                    'customer_name': 'string',
                    'order_state': 'string',
                    'order_amount_untaxed': 'float',
                    'order_amount_tax': 'float',
                    'order_amount_total': 'float',
                },
                'non_nullable_fields': ['order_id', 'order_name', 'order_amount_total'],
            },
            'sales_order_lines': {
                'required_fields': [
                    'order_line_id', 'order_id', 'product_name',
                    'price_unit', 'qty',
                ],
                'field_types': {
                    'order_line_id': 'int',
                    'order_id': 'int',
                    'name': 'string',
                    'product_name': 'string',
                    'product_barcode': 'string',
                    'price_without_tax': 'float',
                    'price_with_tax': 'float',
                    'price_unit': 'float',
                    'qty': 'float',
                },
                'non_nullable_fields': ['order_line_id', 'order_id', 'qty'],
            },
        }

        return schemas.get(entity_type, {})

    def fetch_data(self, entity_type: str, page: int = 1,
                   per_page: Optional[int] = None,
                   order_name: Optional[str] = None) -> Dict:
        """
        Fetch data from the Odoo API for a specific entity type.

        Args:
            entity_type: Type of entity (sales_orders, sales_order_lines)
            page: Unused – Odoo sale order endpoint is not paginated
            per_page: Unused – Odoo sale order endpoint is not paginated
            order_name: Sale order reference (e.g. 'S118658')

        Returns:
            API response containing order data
        """
        endpoint_map = {
            'sales_orders': '/api/sale/order',
            'sales_order_lines': '/api/sale/order',
        }

        endpoint = endpoint_map.get(entity_type)
        if not endpoint:
            raise APIAdapterError(
                f"Unsupported entity type: {entity_type}. "
                f"Supported types: {list(endpoint_map.keys())}"
            )

        params: Dict[str, Any] = {}
        if order_name:
            params['order_name'] = order_name

        return self._make_request(endpoint, params=params)

    def _extract_data_from_response(self, response: Dict) -> List[Dict]:
        """
        Extract the order record(s) from an Odoo API response.

        Odoo returns a single ``order`` dict rather than a list, so this
        method normalises the response into a one-element list so that the
        generic pipeline can iterate over it uniformly.

        Args:
            response: API response dictionary

        Returns:
            List containing the order record (may be empty)
        """
        order = response.get('order')
        if order:
            # Attach order_lines to the order record for convenience
            order['order_lines'] = response.get('order_lines', [])
            return [order]
        return []

    def extract_order_lines(self, response: Dict) -> List[Dict]:
        """
        Extract order line records from an Odoo API response.

        Args:
            response: API response dictionary

        Returns:
            List of order line records
        """
        return response.get('order_lines', [])

    def _has_more_pages(self, response: Dict) -> bool:
        """
        The Odoo sale order endpoint returns a single record per request,
        so there are never additional pages.

        Args:
            response: API response dictionary

        Returns:
            Always False
        """
        return False

    def get_supported_entities(self) -> List[str]:
        """
        Get list of supported entity types for the Odoo API.

        Returns:
            List of entity type names
        """
        return ['sales_orders', 'sales_order_lines']
