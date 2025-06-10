#!/usr/bin/env python3
"""
MTET Platform Startup Script

This script starts the MTET Platform API server with proper configuration.
"""

import uvicorn
import argparse
import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.core.config import get_settings
from app.db.init_db import init_database, create_initial_data


def setup_database():
    """Initialize database if needed."""
    try:
        print("🔄 Initializing database...")
        init_database()
        create_initial_data()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("Please check your database configuration in .env file")
        return False
    return True


def main():
    """Main function to start the MTET Platform."""
    parser = argparse.ArgumentParser(description="MTET Platform API Server")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--init-db", 
        action="store_true", 
        help="Initialize database before starting"
    )
    parser.add_argument(
        "--skip-db-check", 
        action="store_true", 
        help="Skip database initialization check"
    )
    
    args = parser.parse_args()
    
    # Get settings
    settings = get_settings()
    
    print("🚀 Starting MTET Platform API Server")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    
    # Initialize database if requested or if in development
    if args.init_db or (settings.ENVIRONMENT == "development" and not args.skip_db_check):
        if not setup_database():
            sys.exit(1)
    
    # Check if .env file exists
    env_file = current_dir / ".env"
    if not env_file.exists():
        print("⚠️  No .env file found. Using default configuration.")
        print("💡 Copy .env.example to .env and update the values for your environment.")
    
    try:
        # Start the server
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=settings.LOG_LEVEL.lower()
        )
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
