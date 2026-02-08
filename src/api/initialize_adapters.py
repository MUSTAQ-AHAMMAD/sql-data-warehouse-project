"""
Initialize API adapters and register them with the data source registry.
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.data_source_registry import get_registry
from src.api.salla_adapter import SallaAPIAdapter


def initialize_adapters():
    """
    Initialize and register all API adapters.
    """
    registry = get_registry()
    
    # Register Salla adapter
    registry.register_adapter('salla', SallaAPIAdapter)
    
    print("API adapters initialized successfully")
    print(f"Registered sources: {registry.list_sources()}")
    
    return registry


if __name__ == '__main__':
    initialize_adapters()
