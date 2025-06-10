"""
Database configuration and connection management for the MTET Platform

This module handles SQLAlchemy database connections, session management,
and provides the base configuration for database operations.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.core.config import get_settings

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = settings.get_database_url()

# Database engine configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for testing
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # PostgreSQL configuration for production/development
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=20,
        max_overflow=0,
        echo=settings.DEBUG
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Metadata convention for consistent naming
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Base class for all database models
Base = declarative_base(metadata=metadata)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_tables():
    """
    Drop all database tables.
    Warning: This will delete all data!
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


class DatabaseManager:
    """
    Database manager class for advanced database operations.
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            Session: New database session
        """
        return self.SessionLocal()
    
    def execute_raw_query(self, query: str, params: dict = None) -> list:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            list: Query results
        """
        with self.engine.connect() as connection:
            result = connection.execute(query, params or {})
            return result.fetchall()
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a database backup.
        
        Args:
            backup_path: Path to save backup file
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        # Implementation depends on database type
        # This is a placeholder for future implementation
        logger.warning("Database backup not implemented yet")
        return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore successful, False otherwise
        """
        # Implementation depends on database type
        # This is a placeholder for future implementation
        logger.warning("Database restore not implemented yet")
        return False
    
    def get_table_info(self, table_name: str) -> dict:
        """
        Get information about a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            dict: Table information
        """
        try:
            with self.engine.connect() as connection:
                # Get table columns
                if DATABASE_URL.startswith("postgresql"):
                    query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %(table_name)s
                    ORDER BY ordinal_position;
                    """
                elif DATABASE_URL.startswith("sqlite"):
                    query = f"PRAGMA table_info({table_name})"
                else:
                    query = f"DESCRIBE {table_name}"
                
                result = connection.execute(query, {"table_name": table_name})
                columns = result.fetchall()
                
                return {
                    "table_name": table_name,
                    "columns": [dict(row) for row in columns]
                }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {"error": str(e)}
    
    def get_database_stats(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            dict: Database statistics
        """
        try:
            stats = {
                "connection_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
                "engine_info": str(self.engine.url),
                "pool_info": {
                    "size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "invalid": self.engine.pool.invalidated()
                } if hasattr(self.engine.pool, 'size') else "N/A"
            }
            
            # Get table count
            with self.engine.connect() as connection:
                if DATABASE_URL.startswith("postgresql"):
                    result = connection.execute(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                    )
                elif DATABASE_URL.startswith("sqlite"):
                    result = connection.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    )
                else:
                    result = connection.execute("SHOW TABLES")
                
                stats["table_count"] = result.scalar()
            
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}


# Global database manager instance
db_manager = DatabaseManager()


# Database health check function
async def database_health_check() -> dict:
    """
    Async database health check for API endpoints.
    
    Returns:
        dict: Health check results
    """
    try:
        # Check basic connection
        connection_status = check_database_connection()
        
        # Get basic stats
        stats = db_manager.get_database_stats()
        
        return {
            "status": "healthy" if connection_status else "unhealthy",
            "connection": "active" if connection_status else "failed",
            "database_type": "postgresql" if "postgresql" in DATABASE_URL else "sqlite",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Transaction context manager
class DatabaseTransaction:
    """
    Context manager for database transactions.
    """
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.should_close = db is None
    
    def __enter__(self) -> Session:
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
        else:
            self.db.commit()
        
        if self.should_close:
            self.db.close()


# Utility functions for common database operations
def bulk_insert(model_class, data_list: list, batch_size: int = 1000) -> int:
    """
    Bulk insert data into database.
    
    Args:
        model_class: SQLAlchemy model class
        data_list: List of dictionaries with data to insert
        batch_size: Size of each batch for insertion
        
    Returns:
        int: Number of records inserted
    """
    inserted_count = 0
    
    with DatabaseTransaction() as db:
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            objects = [model_class(**data) for data in batch]
            db.bulk_save_objects(objects)
            inserted_count += len(objects)
    
    return inserted_count


def bulk_update(model_class, data_list: list, batch_size: int = 1000) -> int:
    """
    Bulk update data in database.
    
    Args:
        model_class: SQLAlchemy model class
        data_list: List of dictionaries with data to update
        batch_size: Size of each batch for update
        
    Returns:
        int: Number of records updated
    """
    updated_count = 0
    
    with DatabaseTransaction() as db:
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            for data in batch:
                db.bulk_update_mappings(model_class, [data])
            updated_count += len(batch)
    
    return updated_count
