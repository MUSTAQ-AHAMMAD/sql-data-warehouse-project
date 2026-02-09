#!/usr/bin/env python3
"""
Start the Health Monitoring Dashboard

Usage:
    python start_monitoring.py [--port PORT] [--host HOST] [--debug]
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from monitoring.health_dashboard import app, logger, DASHBOARD_HOST, DASHBOARD_PORT, DASHBOARD_DEBUG


def main():
    """Main entry point for monitoring dashboard"""
    parser = argparse.ArgumentParser(description='Start the Health Monitoring Dashboard')
    parser.add_argument('--port', type=int, default=DASHBOARD_PORT,
                       help=f'Port to run the dashboard on (default: {DASHBOARD_PORT})')
    parser.add_argument('--host', type=str, default=DASHBOARD_HOST,
                       help=f'Host to run the dashboard on (default: {DASHBOARD_HOST})')
    parser.add_argument('--debug', action='store_true', default=DASHBOARD_DEBUG,
                       help='Run in debug mode')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("Health Monitoring Dashboard")
    logger.info("="*80)
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Dashboard URL: http://{args.host}:{args.port}")
    logger.info("="*80)
    
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
