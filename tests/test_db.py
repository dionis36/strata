import os
import pytest
from sqlalchemy import create_engine, inspect
from infrastructure.persistence.models import Base

@pytest.fixture
def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    # Initialize the tables using our SQLAlchemy Base
    Base.metadata.create_all(engine)
    return engine

def test_schema_creation(test_engine):
    """Test that all required Phase 0 tables are created by Base.metadata.create_all."""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    
    assert "project" in tables
    assert "analysis_run" in tables
    assert "schema_version" in tables
