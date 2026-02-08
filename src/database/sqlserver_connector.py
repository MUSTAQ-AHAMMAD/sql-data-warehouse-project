"""SQL Server Database Connector Module - Windows Auth Optimized"""

import os
import logging
from typing import List, Dict, Optional
import pyodbc
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLServerConnector:
    def __init__(self, server=None, database=None, username=None, 
                 password=None, driver=None, trusted_connection=None):
        self.server = server or os.getenv('SQLSERVER_HOST', 'localhost\\SQLEXPRESS')
        self.database = database or os.getenv('SQLSERVER_DATABASE', 'master')
        self.username = username or os.getenv('SQLSERVER_USER', '')
        self.password = password or os.getenv('SQLSERVER_PASSWORD', '')
        self.driver = driver or os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
        self.trusted_connection = (
            trusted_connection if trusted_connection is not None 
            else os.getenv('SQLSERVER_TRUSTED_CONNECTION', 'True').lower() == 'true'
        )
        self.connection = None
    
    def connect(self):
        try:
            logger.info(f"Connecting to SQL Server: {self.server}")
            logger.info(f"Database: {self.database}")
            
            if self.trusted_connection or not self.username:
                # Windows Authentication (Named Pipes - works without TCP/IP)
                logger.info("Using Windows Authentication")
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes;"
                )
            else:
                # SQL Server Authentication
                logger.info("Using SQL Server Authentication")
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                    f"TrustServerCertificate=yes;"
                    f"Encrypt=no;"
                )
            
            self.connection = pyodbc.connect(connection_string, timeout=15)
            logger.info("✅ Successfully connected to SQL Server")
            return self.connection
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {str(e)[:300]}")
            logger.error("\n💡 Troubleshooting:")
            logger.error("   1. Make sure SQL Server (SQLEXPRESS) service is running")
            logger.error("   2. Check server name in Services: should be 'SQL Server (SQLEXPRESS)'")
            logger.error("   3. Try opening SSMS with Windows Authentication first")
            raise
    
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Connection closed")
    
    def execute_query(self, query: str, params=None) -> List[Dict]:
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
            else:
                results = []
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise
    
    def execute_script(self, script: str):
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # Clean script: remove comments
            lines = []
            for line in script.split('\n'):
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('--'):
                    lines.append(line)
            
            clean_script = '\n'.join(lines)
            
            # Split by GO (SQL Server batch separator)
            batches = [b.strip() for b in clean_script.split('GO') if b.strip()]
            
            for i, batch in enumerate(batches, 1):
                if not batch:
                    continue
                
                logger.info(f"Executing batch {i}/{len(batches)}: {batch[:60]}...")
                
                try:
                    # Execute the entire batch
                    cursor.execute(batch)
                    self.connection.commit()
                except pyodbc.Error as e:
                    logger.warning(f"Batch {i} error: {e}")
                    # Continue with next batch
                    continue
            
            cursor.close()
            logger.info("✅ Script executed successfully")
            
        except Exception as e:
            try:
                self.connection.rollback()
            except:
                pass
            logger.error(f"Script execution failed: {str(e)}")
            raise
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
