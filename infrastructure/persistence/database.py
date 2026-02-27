import os
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

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
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

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
