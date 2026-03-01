from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from infrastructure.persistence.database import Base

class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

class AnalysisRun(Base):
    __tablename__ = "analysis_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # e.g., 'started', 'completed', 'failed'
    total_files = Column(Integer, nullable=True)
    total_classes = Column(Integer, nullable=True)
    total_edges = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)

class SchemaVersion(Base):
    __tablename__ = "schema_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String, nullable=False, unique=True)
    applied_at = Column(DateTime, default=func.now(), nullable=False)

class ComponentMetric(Base):
    __tablename__ = "component_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("analysis_run.id"), nullable=False)
    component_name = Column(String, nullable=False)
    component_type = Column(String, nullable=False, default="class")  # Phase D: node type
    in_degree = Column(Integer, default=0)
    out_degree = Column(Integer, default=0)
    weighted_in = Column(Integer, default=0)
    weighted_out = Column(Integer, default=0)
    betweenness = Column(Float, default=0.0)
    closeness = Column(Float, default=0.0)
    scc_id = Column(Integer, default=0)
    scc_size = Column(Integer, default=0)
    blast_radius = Column(Integer, default=0)
    fan_in_ratio = Column(Float, default=0.0)
    fan_out_ratio = Column(Float, default=0.0)
    scc_density = Column(Float, default=0.0)
    reachability_ratio = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
