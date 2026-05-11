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

class ComponentBehavior(Base):
    """Phase 4: Behavioral metrics (database write dependencies)."""
    __tablename__ = "component_behavior"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("analysis_run.id"), nullable=False)
    component_name = Column(String, nullable=False)
    write_intensity = Column(Float, default=0.0)
    table_dependencies = Column(Integer, default=0)
    shared_table_pressure = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

class ComponentRisk(Base):
    """Phase 3 & 4: Structural risk scores and behavioral amplification."""
    __tablename__ = "component_risk"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    run_id            = Column(Integer, ForeignKey("analysis_run.id"), nullable=False)
    component_name    = Column(String, nullable=False)
    component_type    = Column(String, nullable=False, default="class")

    # Normalized Phase 2 inputs (min-max per run)
    norm_betweenness  = Column(Float, default=0.0)
    norm_blast_radius = Column(Float, default=0.0)
    norm_in_degree    = Column(Float, default=0.0)
    norm_out_degree   = Column(Float, default=0.0)

    # Derived structural indicators
    criticality_index = Column(Float, default=0.0)
    instability       = Column(Float, default=0.0)
    cycle_flag        = Column(Integer, default=0)
    coupling_pressure = Column(Float, default=0.0)

    # Risk output (Phase 3)
    risk_score        = Column(Float, nullable=False)
    risk_level        = Column(String, nullable=False)

    # Behavioral Intelligence (Phase 4)
    behavioral_factor = Column(Float, default=0.0)
    final_risk        = Column(Float, nullable=False, default=0.0)


    created_at        = Column(DateTime, default=func.now(), nullable=False)

class ComponentDependency(Base):
    """
    Phase 3: Persists the graph edges directly in SQLite.
    Enables recursive queries for blast-radius and impact analysis.
    """
    __tablename__ = "component_dependencies"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    run_id      = Column(Integer, ForeignKey("analysis_run.id"), nullable=False)
    source_id   = Column(String, nullable=False)
    target_id   = Column(String, nullable=False)
    edge_type   = Column(String, nullable=False)
    
    created_at  = Column(DateTime, default=func.now(), nullable=False)
