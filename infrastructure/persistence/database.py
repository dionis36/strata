import os
import logging
import sqlite3
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# We resolve the DATABASE_URL. In local local dev, we might use a relative path if /data isn't mapped
# This logic accommodates the Docker `/data/app.db` path vs local `./data/app.db`
db_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
if db_url.startswith("sqlite:////data/"):
    # If not running in docker but string says /data/, let's fallback to relative for pure local testing
    if not os.path.exists("/data") and os.path.exists("./data"):
        db_url = "sqlite:///./data/app.db"

# Engine setup
engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False, "timeout": 15} if "sqlite" in db_url else {}
)

from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in db_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logger = logging.getLogger(__name__)

def init_db() -> None:
    """
    Initializes the database, creating all tables defined in Base,
    and inserts the initial schema version if empty.
    """
    # Import models here to ensure they are registered with Base
    from infrastructure.persistence import models 
    from sqlalchemy.exc import SQLAlchemyError
    from datetime import datetime
    import pytz

    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized: Tables created if not existed at {db_url}")

        # If running against an existing SQLite DB that predates new AI columns, ensure they exist
        try:
            if engine.dialect.name == "sqlite":
                sqlite_db_path = engine.url.database
                if sqlite_db_path and os.path.exists(sqlite_db_path):
                    try:
                        conn_sql = sqlite3.connect(sqlite_db_path)
                        cur = conn_sql.cursor()
                        cur.execute("PRAGMA table_info('analysis_run')")
                        existing_cols = [row[1] for row in cur.fetchall()]
                        for col in ("ai_executive_summary_json", "ai_findings_json", "ai_rector_config_json"):
                            if col not in existing_cols:
                                cur.execute(f"ALTER TABLE analysis_run ADD COLUMN {col} TEXT")
                                
                        # New Deep Intelligence Metrics (Phase 6)
                        for table_name in ("component_metrics", "component_risk"):
                            cur.execute(f"PRAGMA table_info('{table_name}')")
                            existing_tbl_cols = [row[1] for row in cur.fetchall()]
                            if "halstead_effort" not in existing_tbl_cols:
                                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN halstead_effort REAL")
                            if "pagerank" not in existing_tbl_cols:
                                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN pagerank REAL")
                            if "lloc" not in existing_tbl_cols:
                                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN lloc INTEGER")
                                
                        conn_sql.commit()
                        conn_sql.close()
                        logger.info("Ensured AI and Deep Intelligence columns are present in DB")
                    except Exception as e:
                        logger.error(f"Failed to ensure AI columns in sqlite DB: {e}")
        except Exception:
            # Non-fatal: if dialect or path introspection fails, continue to schema versioning
            pass

        # Enforce schema version on startup
        db = SessionLocal()
        try:
            version_count = db.query(models.SchemaVersion).count()
            if version_count == 0:
                initial_version = models.SchemaVersion(
                    version="0.1",
                    applied_at=datetime.utcnow()
                )
                db.add(initial_version)
                db.commit()
                logger.info("Inserted initial schema_version 0.1")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to insert schema version: {e}")
            raise
        finally:
            db.close()

    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_db() -> Generator:
    """
    Dependency generator for FastAPI to yield a DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
