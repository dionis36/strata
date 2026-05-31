from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from infrastructure.persistence.database import Base

class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    root_path = Column(String, nullable=True)  # Persisted for one-click rescanning
    created_at = Column(DateTime, default=func.now(), nullable=False)

class AnalysisRun(Base):
    __tablename__ = "analysis_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # e.g., 'started', 'completed', 'failed'
    
    # Aggregate Metrics (A. Dashboard)
    total_files = Column(Integer, nullable=True)
    total_loc = Column(Integer, nullable=True)
    avg_complexity = Column(Float, nullable=True)
    avg_maintainability = Column(Float, nullable=True)
    
    total_classes = Column(Integer, nullable=True)
    total_methods = Column(Integer, nullable=True)
    total_functions = Column(Integer, nullable=True)
    total_namespaces = Column(Integer, nullable=True)
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
    
    # Phase 5: Semantic Intelligence
    domain_archetype = Column(String, nullable=True)
    is_stateful = Column(Boolean, default=False)
    lcom = Column(Float, default=0.0)
    wmc = Column(Integer, default=0)
    
    # Phase 8: Test Coverage Awareness
    test_coverage = Column(Float, nullable=True)
    
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
    
    # Semantic Intelligence (Phase 5)
    domain_archetype = Column(String, nullable=True)
    is_stateful = Column(Boolean, default=False)
    lcom = Column(Float, default=0.0)
    wmc = Column(Integer, default=0)
    semantic_multiplier = Column(Float, default=1.0)
    
    # Phase 8: Test Coverage Awareness
    test_coverage = Column(Float, nullable=True)
    
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

class FileCache(Base):
    """
    Module C.2: Incremental Analysis Cache.
    Stores the hash and serialized AST results for each file.
    """
    __tablename__ = "file_cache"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    file_path   = Column(String, nullable=False, index=True)
    file_hash   = Column(String, nullable=False)
    nodes_data  = Column(String, nullable=False)  # Serialized Node list
    edges_data  = Column(String, nullable=False)  # Serialized Edge list
    
    updated_at  = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class LegacyMetrics(Base):
    """
    Requirements 1, 8, 9: specialized modernization indicators.
    Stores the 'Specialist' insights about the legacy environment.
    """
    __tablename__ = "legacy_metrics"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    run_id         = Column(Integer, ForeignKey("analysis_run.id"), nullable=False)
    
    # Requirement 1: Era Classification
    php_era        = Column(String, nullable=True) # Era A, B, C, D
    
    # Requirement 8: Modernization Score Dimensions
    version_score  = Column(Float, default=0.0)
    namespace_score = Column(Float, default=0.0)
    db_layer_score = Column(Float, default=0.0)
    security_score = Column(Float, default=0.0)
    testability_score = Column(Float, default=0.0)
    coupling_score = Column(Float, default=0.0)
    total_modernization_score = Column(Float, default=0.0)
    
    # Requirement 9: Framework Fingerprinting
    detected_framework = Column(String, nullable=True)
    
    # Requirement 15: Hosting Assumptions
    hosting_risk_level = Column(String, nullable=True)
    
    # Phase 3: Deep Technical Profiling (Req 10-13)
    db_layer           = Column(String, nullable=True)
    auth_layer         = Column(String, nullable=True)
    template_layer     = Column(String, nullable=True)
    autoloading_strategy = Column(String, nullable=True)
    
    created_at     = Column(DateTime, default=func.now(), nullable=False)


class GraphNode(Base):
    """
    Phase 4: Normalized AST node storage.
    Represents classes, methods, functions, tables, namespaces, etc.
    """
    __tablename__ = "graph_nodes"

    id            = Column(String, primary_key=True)  # Deterministic Hash ID
    run_id        = Column(Integer, ForeignKey("analysis_run.id"), primary_key=True)
    name          = Column(String, nullable=False)
    fqn           = Column(String, nullable=False)
    node_type     = Column(String, nullable=False)  # class, method, table, etc.
    namespace     = Column(String, nullable=True)
    file_path     = Column(String, nullable=True)
    metadata_json = Column(String, nullable=True)   # Serialized raw attributes/AST info
    created_at    = Column(DateTime, default=func.now(), nullable=False)


class GraphEdge(Base):
    """
    Phase 4: Normalized AST edge storage.
    Connects GraphNodes representing dependencies.
    """
    __tablename__ = "graph_edges"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    run_id      = Column(Integer, ForeignKey("analysis_run.id"), nullable=False)
    source_id   = Column(String, nullable=False)
    target_id   = Column(String, nullable=False)
    edge_type   = Column(String, nullable=False)  # CALLS, DECLARES, INHERITS, etc.
    created_at  = Column(DateTime, default=func.now(), nullable=False)
