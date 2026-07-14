from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import AnalysisRun, GraphNode
db = SessionLocal()
run = db.query(AnalysisRun).filter(AnalysisRun.id == 8).first()
print(f"Run {run.id} status: {run.status}")
nodes = db.query(GraphNode).filter(GraphNode.run_id == 8).count()
print(f"GraphNodes for run 8: {nodes}")
