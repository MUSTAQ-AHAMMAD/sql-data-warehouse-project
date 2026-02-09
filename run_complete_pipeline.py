"""
Complete Data Warehouse Pipeline Orchestrator

End-to-end pipeline orchestration with:
- Pre-flight health checks
- Data extraction (API or sample data)
- Bronze → Silver → Gold transformations
- Power BI view creation
- Data quality verification
- Comprehensive logging and error handling
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database.database_factory import get_database_connector, get_database_type
from src.transformations.bronze_extractor_production import BronzeExtractorProduction
from src.transformations.universal_transformer import UniversalTransformer
from src.powerbi.powerbi_connector import PowerBIConnector

load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CompletePipelineOrchestrator:
    """
    Orchestrates the complete data warehouse pipeline from extraction to reporting.
    
    Features:
    - Pre-flight health checks
    - Dual mode: API or sample data
    - Bronze → Silver → Gold transformations
    - Power BI view creation
    - Data quality verification
    - Execution summary with statistics
    """
    
    def __init__(self, use_sample_data: bool = None):
        """
        Initialize the pipeline orchestrator.
        
        Args:
            use_sample_data: If True, uses sample data. If None, auto-detects based on API token
        """
        self.db = get_database_connector()
        self.db_type = get_database_type()
        self.execution_start_time = None
        self.execution_stats = {
            'bronze_orders': 0,
            'bronze_customers': 0,
            'bronze_products': 0,
            'silver_orders': 0,
            'silver_customers': 0,
            'silver_products': 0,
            'gold_dims': 0,
            'gold_facts': 0,
            'powerbi_views': 0,
            'errors': []
        }
        
        # Auto-detect sample data mode if not specified
        if use_sample_data is None:
            api_token = os.getenv('SALLA_API_TOKEN')
            self.use_sample_data = not api_token or api_token == 'your_bearer_token_here'
        else:
            self.use_sample_data = use_sample_data
        
        logger.info(f"Initialized orchestrator for {self.db_type.upper()}")
        logger.info(f"Data mode: {'SAMPLE DATA' if self.use_sample_data else 'API'}")
    
    def run_preflight_checks(self) -> bool:
        """
        Run pre-flight health checks before pipeline execution.
        
        Returns:
            True if all checks pass, False otherwise
        """
        logger.info("=" * 80)
        logger.info("RUNNING PRE-FLIGHT HEALTH CHECKS")
        logger.info("=" * 80)
        
        checks_passed = True
        
        # Check 1: Database connectivity
        logger.info("\n1️⃣ Checking database connectivity...")
        try:
            with self.db as conn:
                if self.db_type == 'sqlserver':
                    result = conn.execute_query("SELECT @@VERSION as version")
                    logger.info(f"   ✅ Connected to SQL Server")
                    logger.info(f"   Version: {result[0]['version'][:50]}...")
                elif self.db_type == 'snowflake':
                    result = conn.execute_query("SELECT CURRENT_VERSION()")
                    logger.info(f"   ✅ Connected to Snowflake")
                    logger.info(f"   Version: {result[0][0]}")
        except Exception as e:
            logger.error(f"   ❌ Database connection failed: {str(e)}")
            checks_passed = False
        
        # Check 2: Required tables exist
        logger.info("\n2️⃣ Checking required tables...")
        required_tables = [
            ('BRONZE', 'bronze_orders'),
            ('BRONZE', 'bronze_customers'),
            ('BRONZE', 'bronze_products'),
            ('SILVER', 'silver_orders'),
            ('SILVER', 'silver_customers'),
            ('SILVER', 'silver_products'),
            ('GOLD', 'gold_dim_customers'),
            ('GOLD', 'gold_dim_products'),
            ('GOLD', 'gold_fact_orders')
        ]
        
        try:
            with self.db as conn:
                for schema, table in required_tables:
                    query = f"""
                        SELECT COUNT(*) as cnt 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = '{schema}' 
                        AND TABLE_NAME = '{table}'
                    """
                    result = conn.execute_query(query)
                    if result[0]['cnt'] > 0:
                        logger.info(f"   ✅ {schema}.{table} exists")
                    else:
                        logger.warning(f"   ⚠️ {schema}.{table} not found")
        except Exception as e:
            logger.error(f"   ❌ Table check failed: {str(e)}")
            checks_passed = False
        
        # Check 3: API token (if not using sample data)
        if not self.use_sample_data:
            logger.info("\n3️⃣ Checking API configuration...")
            api_token = os.getenv('SALLA_API_TOKEN')
            if api_token and api_token != 'your_bearer_token_here':
                logger.info("   ✅ API token configured")
            else:
                logger.warning("   ⚠️ API token not configured - falling back to sample data")
                self.use_sample_data = True
        
        logger.info("\n" + "=" * 80)
        if checks_passed:
            logger.info("✅ PRE-FLIGHT CHECKS PASSED")
        else:
            logger.error("❌ PRE-FLIGHT CHECKS FAILED")
        logger.info("=" * 80 + "\n")
        
        return checks_passed
    
    def extract_bronze_layer(self) -> bool:
        """
        Extract data to Bronze layer.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 80)
        logger.info("PHASE 1: BRONZE LAYER EXTRACTION")
        logger.info("=" * 80)
        
        try:
            extractor = BronzeExtractorProduction(use_sample_data=self.use_sample_data)
            
            # Extract orders
            orders_count = extractor.extract_orders(incremental=True)
            self.execution_stats['bronze_orders'] = orders_count
            
            # Extract customers
            customers_count = extractor.extract_customers(incremental=True)
            self.execution_stats['bronze_customers'] = customers_count
            
            # Extract products
            products_count = extractor.extract_products(incremental=True)
            self.execution_stats['bronze_products'] = products_count
            
            logger.info("=" * 80)
            logger.info("✅ BRONZE LAYER EXTRACTION COMPLETE")
            logger.info(f"   Orders: {orders_count}")
            logger.info(f"   Customers: {customers_count}")
            logger.info(f"   Products: {products_count}")
            logger.info("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Bronze extraction failed: {str(e)}")
            self.execution_stats['errors'].append(f"Bronze extraction: {str(e)}")
            return False
    
    def transform_silver_layer(self) -> bool:
        """
        Transform Bronze to Silver layer.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 80)
        logger.info("PHASE 2: SILVER LAYER TRANSFORMATION")
        logger.info("=" * 80)
        
        try:
            transformer = UniversalTransformer()
            
            # Transform orders
            orders_count = transformer.transform_bronze_to_silver('orders')
            self.execution_stats['silver_orders'] = orders_count
            
            # Transform customers
            customers_count = transformer.transform_bronze_to_silver('customers')
            self.execution_stats['silver_customers'] = customers_count
            
            # Transform products
            products_count = transformer.transform_bronze_to_silver('products')
            self.execution_stats['silver_products'] = products_count
            
            logger.info("=" * 80)
            logger.info("✅ SILVER LAYER TRANSFORMATION COMPLETE")
            logger.info(f"   Orders: {orders_count}")
            logger.info(f"   Customers: {customers_count}")
            logger.info(f"   Products: {products_count}")
            logger.info("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Silver transformation failed: {str(e)}")
            self.execution_stats['errors'].append(f"Silver transformation: {str(e)}")
            return False
    
    def transform_gold_layer(self) -> bool:
        """
        Transform Silver to Gold layer.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 80)
        logger.info("PHASE 3: GOLD LAYER TRANSFORMATION")
        logger.info("=" * 80)
        
        try:
            transformer = UniversalTransformer()
            
            # Transform dimensions
            dim_customers = transformer.transform_silver_to_gold('dim_customers')
            dim_products = transformer.transform_silver_to_gold('dim_products')
            self.execution_stats['gold_dims'] = dim_customers + dim_products
            
            # Transform facts
            fact_orders = transformer.transform_silver_to_gold('fact_orders')
            self.execution_stats['gold_facts'] = fact_orders
            
            logger.info("=" * 80)
            logger.info("✅ GOLD LAYER TRANSFORMATION COMPLETE")
            logger.info(f"   Dim Customers: {dim_customers}")
            logger.info(f"   Dim Products: {dim_products}")
            logger.info(f"   Fact Orders: {fact_orders}")
            logger.info("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Gold transformation failed: {str(e)}")
            self.execution_stats['errors'].append(f"Gold transformation: {str(e)}")
            return False
    
    def create_powerbi_views(self) -> bool:
        """
        Create Power BI views for reporting.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 80)
        logger.info("PHASE 4: POWER BI VIEW CREATION")
        logger.info("=" * 80)
        
        try:
            connector = PowerBIConnector()
            
            # Create all views
            connector.create_all_views()
            
            # Test views
            view_counts = connector.test_views()
            self.execution_stats['powerbi_views'] = len(view_counts)
            
            logger.info("=" * 80)
            logger.info("✅ POWER BI VIEWS CREATED")
            logger.info(f"   Total views: {len(view_counts)}")
            for view, count in view_counts.items():
                logger.info(f"   {view}: {count} rows")
            logger.info("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Power BI view creation failed: {str(e)}")
            self.execution_stats['errors'].append(f"Power BI views: {str(e)}")
            return False
    
    def verify_data_quality(self) -> bool:
        """
        Verify data quality across all layers.
        
        Returns:
            True if quality checks pass, False otherwise
        """
        logger.info("=" * 80)
        logger.info("PHASE 5: DATA QUALITY VERIFICATION")
        logger.info("=" * 80)
        
        try:
            with self.db as conn:
                # Get counts from all layers
                query = """
                    SELECT 
                        (SELECT COUNT(*) FROM BRONZE.bronze_orders) as bronze_orders,
                        (SELECT COUNT(*) FROM SILVER.silver_orders) as silver_orders,
                        (SELECT COUNT(*) FROM GOLD.gold_fact_orders) as gold_orders
                """
                result = conn.execute_query(query)
                
                bronze_count = result[0]['bronze_orders']
                silver_count = result[0]['silver_orders']
                gold_count = result[0]['gold_orders']
                
                logger.info(f"\n📊 Data Quality Metrics:")
                logger.info(f"   Bronze Orders: {bronze_count:,}")
                logger.info(f"   Silver Orders: {silver_count:,}")
                logger.info(f"   Gold Orders: {gold_count:,}")
                
                # Quality checks
                issues = []
                
                if bronze_count == 0:
                    issues.append("No data in Bronze layer")
                
                if silver_count < bronze_count * 0.9:
                    issues.append(f"Significant data loss in Silver layer: {bronze_count - silver_count} records")
                
                if gold_count < silver_count * 0.9:
                    issues.append(f"Significant data loss in Gold layer: {silver_count - gold_count} records")
                
                if issues:
                    logger.warning("\n⚠️ Data Quality Issues:")
                    for issue in issues:
                        logger.warning(f"   - {issue}")
                        self.execution_stats['errors'].append(f"Quality check: {issue}")
                else:
                    logger.info("\n✅ All data quality checks passed")
                
                logger.info("=" * 80 + "\n")
                
                return len(issues) == 0
                
        except Exception as e:
            logger.error(f"❌ Data quality verification failed: {str(e)}")
            self.execution_stats['errors'].append(f"Quality verification: {str(e)}")
            return False
    
    def print_execution_summary(self):
        """Print comprehensive execution summary."""
        execution_time = time.time() - self.execution_start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"\n⏱️ Execution Time: {execution_time:.2f} seconds")
        
        logger.info(f"\n📥 Bronze Layer:")
        logger.info(f"   Orders: {self.execution_stats['bronze_orders']:,}")
        logger.info(f"   Customers: {self.execution_stats['bronze_customers']:,}")
        logger.info(f"   Products: {self.execution_stats['bronze_products']:,}")
        
        logger.info(f"\n🔄 Silver Layer:")
        logger.info(f"   Orders: {self.execution_stats['silver_orders']:,}")
        logger.info(f"   Customers: {self.execution_stats['silver_customers']:,}")
        logger.info(f"   Products: {self.execution_stats['silver_products']:,}")
        
        logger.info(f"\n⭐ Gold Layer:")
        logger.info(f"   Dimensions: {self.execution_stats['gold_dims']:,}")
        logger.info(f"   Facts: {self.execution_stats['gold_facts']:,}")
        
        logger.info(f"\n📊 Power BI:")
        logger.info(f"   Views Created: {self.execution_stats['powerbi_views']}")
        
        if self.execution_stats['errors']:
            logger.error(f"\n❌ Errors ({len(self.execution_stats['errors'])}):")
            for error in self.execution_stats['errors']:
                logger.error(f"   - {error}")
        else:
            logger.info(f"\n✅ No errors encountered")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 PIPELINE EXECUTION COMPLETE")
        logger.info("=" * 80 + "\n")
    
    def run_complete_pipeline(self) -> bool:
        """
        Run the complete data warehouse pipeline.
        
        Returns:
            True if pipeline completes successfully, False otherwise
        """
        self.execution_start_time = time.time()
        
        logger.info("\n" + "=" * 80)
        logger.info("🚀 STARTING COMPLETE DATA WAREHOUSE PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Database: {self.db_type.upper()}")
        logger.info(f"Data Mode: {'SAMPLE DATA' if self.use_sample_data else 'API'}")
        logger.info("=" * 80 + "\n")
        
        try:
            # Pre-flight checks
            if not self.run_preflight_checks():
                logger.error("Pre-flight checks failed. Aborting pipeline.")
                return False
            
            # Phase 1: Bronze extraction
            if not self.extract_bronze_layer():
                logger.error("Bronze extraction failed. Aborting pipeline.")
                return False
            
            # Phase 2: Silver transformation
            if not self.transform_silver_layer():
                logger.error("Silver transformation failed. Continuing with caution...")
            
            # Phase 3: Gold transformation
            if not self.transform_gold_layer():
                logger.error("Gold transformation failed. Continuing with caution...")
            
            # Phase 4: Power BI views
            if not self.create_powerbi_views():
                logger.error("Power BI view creation failed. Continuing with caution...")
            
            # Phase 5: Data quality verification
            self.verify_data_quality()
            
            # Print execution summary
            self.print_execution_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {str(e)}")
            self.execution_stats['errors'].append(f"Pipeline error: {str(e)}")
            self.print_execution_summary()
            return False


def main():
    """Main entry point for the pipeline orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run complete data warehouse pipeline')
    parser.add_argument('--sample', action='store_true', 
                       help='Use sample data instead of API')
    parser.add_argument('--no-sample', action='store_true',
                       help='Force API usage (will fail if token not configured)')
    
    args = parser.parse_args()
    
    # Determine sample data mode
    use_sample = None
    if args.sample:
        use_sample = True
    elif args.no_sample:
        use_sample = False
    
    # Run pipeline
    orchestrator = CompletePipelineOrchestrator(use_sample_data=use_sample)
    success = orchestrator.run_complete_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
