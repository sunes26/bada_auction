"""
SQLAlchemy-based Database Manager
Supports both PostgreSQL (production) and SQLite (development)
"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from .models import Base


class DatabaseManager:
    """Database manager with SQLAlchemy ORM support"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager

        Args:
            database_url: Database connection URL
                - PostgreSQL: postgresql://user:password@host:port/dbname
                - SQLite: sqlite:///path/to/db.db
                - If None, uses DATABASE_URL env var or defaults to SQLite
        """
        # Get database URL from parameter or environment
        if database_url is None:
            database_url = os.getenv('DATABASE_URL')

        # Default to SQLite if no URL provided
        if database_url is None:
            database_url = 'sqlite:///monitoring.db'

        # Handle Supabase connection pooler URL
        # Supabase provides pooled connections at port 6543
        if 'supabase.co' in database_url and ':5432' in database_url:
            # Convert to pooler connection (6543) for better performance
            database_url = database_url.replace(':5432', ':6543')

        self.database_url = database_url
        self.is_postgresql = database_url.startswith('postgresql')
        self.is_sqlite = database_url.startswith('sqlite')

        # Create engine with appropriate settings
        engine_kwargs = {}

        if self.is_sqlite:
            # SQLite-specific settings
            engine_kwargs['connect_args'] = {'check_same_thread': False}
            engine_kwargs['poolclass'] = StaticPool
        else:
            # PostgreSQL settings
            engine_kwargs['pool_size'] = 10
            engine_kwargs['max_overflow'] = 20
            engine_kwargs['pool_pre_ping'] = True  # Verify connections before using

        self.engine = create_engine(database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_all_tables(self):
        """Create all tables defined in models"""
        Base.metadata.create_all(bind=self.engine)
        print(f"[OK] Tables created successfully on {self.database_url}")

    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        print(f"[OK] All tables dropped from {self.database_url}")

    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session with automatic commit/rollback

        Usage:
            with db_manager.get_session() as session:
                product = session.query(MonitoredProduct).filter_by(id=1).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_db_session(self) -> Session:
        """
        Get a database session for dependency injection

        Usage (FastAPI):
            @app.get("/products")
            def get_products(db: Session = Depends(get_db_session)):
                return db.query(MonitoredProduct).all()
        """
        session = self.SessionLocal()
        try:
            return session
        finally:
            pass  # Session will be closed by FastAPI

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                # Test query (SQLAlchemy 2.0 syntax)
                session.execute(text("SELECT 1"))
            print(f"[OK] Database connection successful: {self.database_url}")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get or create database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database(database_url: Optional[str] = None):
    """
    Initialize database

    Args:
        database_url: Optional database URL override
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    _db_manager.create_all_tables()
    return _db_manager


# FastAPI dependency
def get_db() -> Session:
    """
    FastAPI dependency for getting database session

    Usage:
        @app.get("/products")
        def get_products(db: Session = Depends(get_db)):
            return db.query(MonitoredProduct).all()
    """
    db_manager = get_database_manager()
    db = db_manager.get_db_session()
    try:
        yield db
    finally:
        db.close()
