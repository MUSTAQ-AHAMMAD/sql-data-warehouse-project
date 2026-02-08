#!/usr/bin/env python3
"""
Start the API Testing Dashboard

Usage:
    python start_dashboard.py [--port PORT] [--host HOST] [--debug]
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Change to dashboard directory
os.chdir(os.path.join(os.path.dirname(__file__), 'dashboard'))

from dashboard.app import app, logger, DASHBOARD_HOST, DASHBOARD_PORT, DASHBOARD_DEBUG


def main():
    """Main entry point for dashboard"""
    parser = argparse.ArgumentParser(description='Start the API Testing Dashboard')
    parser.add_argument('--port', type=int, default=DASHBOARD_PORT,
                       help=f'Port to run the dashboard on (default: {DASHBOARD_PORT})')
    parser.add_argument('--host', type=str, default=DASHBOARD_HOST,
                       help=f'Host to run the dashboard on (default: {DASHBOARD_HOST})')
    parser.add_argument('--debug', action='store_true', default=DASHBOARD_DEBUG,
                       help='Run in debug mode')
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("API Testing Dashboard")
    logger.info("="*60)
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Dashboard URL: http://{args.host}:{args.port}")
    logger.info("="*60)
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down dashboard...")
    except Exception as e:
        logger.error(f"Failed to start dashboard: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
