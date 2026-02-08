"""Create SALLA_DWH database"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.database.sqlserver_connector import SQLServerConnector

def create_database():
    print("🔌 Connecting to SQL Server (master database)...")
    
    # Connect to master database first
    with SQLServerConnector(database='master') as db:
        print("✅ Connected!\n")
        
        # Check if database exists
        print("📊 Checking if SALLA_DWH exists...")
        result = db.execute_query(
            "SELECT name FROM sys.databases WHERE name = 'SALLA_DWH'"
        )
        
        if result:
            print("✅ Database SALLA_DWH already exists\n")
        else:
            print("📝 Creating database SALLA_DWH...")
            db.execute_query("CREATE DATABASE SALLA_DWH")
            print("✅ Database SALLA_DWH created successfully!\n")
        
        # Verify
        result = db.execute_query(
            "SELECT name, create_date FROM sys.databases WHERE name = 'SALLA_DWH'"
        )
        
        if result:
            print(f"✅ Database verified:")
            print(f"   Name: {result[0]['name']}")
            print(f"   Created: {result[0]['create_date']}")
            print("\n🎉 Database setup complete!")
        else:
            print("❌ Database creation failed")

if __name__ == "__main__":
    create_database()
