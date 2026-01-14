"""
Installation Validation Script

This script validates that all dependencies are installed correctly and configurations are set.
"""

import sys
import os
from typing import List, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        return True, f"✓ Python {version.major}.{version.minor}.{version.micro}"
    return False, f"✗ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)"


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, f"✓ {package_name}"
    except ImportError:
        return False, f"✗ {package_name} not installed"


def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists."""
    if os.path.exists('.env'):
        return True, "✓ .env file exists"
    return False, "✗ .env file not found (copy from .env.example)"


def check_env_variables() -> List[Tuple[bool, str]]:
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'SALLA_API_TOKEN',
        'SNOWFLAKE_ACCOUNT',
        'SNOWFLAKE_USER',
        'SNOWFLAKE_PASSWORD',
        'SNOWFLAKE_WAREHOUSE'
    ]
    
    results = []
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}':
            results.append((True, f"✓ {var} is set"))
        else:
            results.append((False, f"✗ {var} not configured"))
    
    return results


def check_directory_structure() -> List[Tuple[bool, str]]:
    """Check if required directories exist."""
    required_dirs = [
        'src/api',
        'src/database',
        'src/transformations',
        'src/utils',
        'dags',
        'sql/bronze',
        'sql/silver',
        'sql/gold',
        'docs'
    ]
    
    results = []
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            results.append((True, f"✓ {dir_path}"))
        else:
            results.append((False, f"✗ {dir_path} missing"))
    
    return results


def check_required_files() -> List[Tuple[bool, str]]:
    """Check if required files exist."""
    required_files = [
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md',
        'src/api/salla_connector.py',
        'src/database/snowflake_connector.py',
        'src/transformations/bronze_extractor.py',
        'src/transformations/silver_transformer.py',
        'src/transformations/gold_transformer.py',
        'dags/salla_bronze_dag.py',
        'dags/salla_silver_dag.py',
        'dags/salla_gold_dag.py'
    ]
    
    results = []
    for file_path in required_files:
        if os.path.isfile(file_path):
            results.append((True, f"✓ {file_path}"))
        else:
            results.append((False, f"✗ {file_path} missing"))
    
    return results


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("SQL Data Warehouse Project - Installation Validation")
    print("=" * 70)
    
    all_passed = True
    
    # Check Python version
    print("\n1. Python Version:")
    print("-" * 70)
    passed, message = check_python_version()
    print(message)
    all_passed &= passed
    
    # Check required packages
    print("\n2. Required Python Packages:")
    print("-" * 70)
    packages = [
        ('apache-airflow', 'airflow'),
        ('snowflake-connector-python', 'snowflake.connector'),
        ('requests', 'requests'),
        ('pandas', 'pandas'),
        ('python-dotenv', 'dotenv'),
        ('tenacity', 'tenacity')
    ]
    
    for pkg_name, import_name in packages:
        passed, message = check_package(pkg_name, import_name)
        print(message)
        all_passed &= passed
    
    # Check .env file
    print("\n3. Configuration File:")
    print("-" * 70)
    passed, message = check_env_file()
    print(message)
    all_passed &= passed
    
    # Check environment variables
    if passed:
        print("\n4. Environment Variables:")
        print("-" * 70)
        for passed, message in check_env_variables():
            print(message)
            all_passed &= passed
    
    # Check directory structure
    print("\n5. Directory Structure:")
    print("-" * 70)
    for passed, message in check_directory_structure():
        print(message)
        all_passed &= passed
    
    # Check required files
    print("\n6. Required Files:")
    print("-" * 70)
    for passed, message in check_required_files():
        print(message)
        all_passed &= passed
    
    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All checks passed! Your installation is complete.")
        print("\nNext steps:")
        print("1. Review and update .env file with your credentials")
        print("2. Run: python src/utils/setup_database.py")
        print("3. Start Airflow: airflow webserver & airflow scheduler")
    else:
        print("✗ Some checks failed. Please review the messages above.")
        print("\nTo fix:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Copy .env.example to .env and configure it")
        print("3. Ensure all required files are present")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
