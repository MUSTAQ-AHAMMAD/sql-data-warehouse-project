import sys
import os
from dotenv import load_dotenv

load_dotenv()

print(f"🐍 Python: {sys.version}")
print(f"📂 Working directory: {os.getcwd()}\n")

# Test pyodbc
try:
    import pyodbc
    print("✅ pyodbc installed")
    drivers = pyodbc.drivers()
    print(f"   ODBC Drivers available:")
    if drivers:
        for driver in drivers:
            print(f"      - {driver}")
    else:
        print("      ⚠️  No ODBC drivers found!")
        print("      Install: ODBC Driver 17 for SQL Server")
except ImportError as e:
    print(f"❌ pyodbc not installed: {e}")
    sys.exit(1)

print()

# Test SQL Server connection
try:
    from src.database.sqlserver_connector import SQLServerConnector
    
    print("🔌 Testing SQL Server connection...")
    print(f"   Host: {os.getenv('SQLSERVER_HOST')}")
    print(f"   Database: {os.getenv('SQLSERVER_DATABASE')}")
    print(f"   User: {os.getenv('SQLSERVER_USER')}\n")
    
    with SQLServerConnector() as sql:
        result = sql.execute_query("SELECT @@VERSION as version, @@SERVERNAME as server")
        print("✅ Connection successful!")
        print(f"   Server: {result[0]['server']}")
        print(f"   Version: {result[0]['version'].split('-')[0].strip()}")
        print()
        print("🎉 Ready to setup database!")
        
except Exception as e:
    print(f"❌ Connection failed: {e}\n")
    print("💡 Troubleshooting checklist:")
    print("   1. SQL Server (SQLEXPRESS) service is running")
    print("   2. Created 'etl_user' login in SSMS")
    print("   3. Created 'SALLA_DWH' database")
    print("   4. ODBC Driver 17 for SQL Server is installed")
    print("   5. Enabled SQL Server Authentication in SSMS")
    print("   6. .env file has correct credentials")
