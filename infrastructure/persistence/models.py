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


class ComponentRisk(Base):
    """Phase 3: Structural risk scores derived from Phase 2 metrics.

    Stored separately from ComponentMetric to keep Phase 2 and Phase 3
    data concerns cleanly separated. All derived indicators are persisted
    to enable Phase 6 ablation studies without re-running analysis.
    """
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

    # Derived structural indicators (Phase 6: ablation targets)
    criticality_index = Column(Float, default=0.0)   # betweenness × blast_radius
    instability       = Column(Float, default=0.0)   # out / (in + out)
    cycle_flag        = Column(Integer, default=0)   # 1 if scc_size > 1
    coupling_pressure = Column(Float, default=0.0)   # (norm_in + norm_out) / 2

    # Risk output
    risk_score        = Column(Float, nullable=False)
    risk_level        = Column(String, nullable=False)  # LOW / MEDIUM / HIGH / CRITICAL

    created_at        = Column(DateTime, default=func.now(), nullable=False)
