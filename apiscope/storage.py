"""Optional scan history storage, no-op when DATABASE_URL is absent."""
import json,uuid
from apiscope.db import engine,SessionLocal,Base
from apiscope.models import ScanRecord
def initialize():
    if engine: Base.metadata.create_all(engine)
def save_scan(scan,source_type="har"):
    if not SessionLocal: return None
    record=ScanRecord(id=str(uuid.uuid4()),source_type=source_type,endpoint_count=scan.get("endpoint_count",0),payload_json=json.dumps(scan))
    with SessionLocal() as db:
        db.add(record);db.commit()
    return record.id
def list_scans(limit=50):
    if not SessionLocal:return []
    with SessionLocal() as db:
        return [{"id":r.id,"created_at":r.created_at.isoformat(),"source_type":r.source_type,"endpoint_count":r.endpoint_count} for r in db.query(ScanRecord).order_by(ScanRecord.created_at.desc()).limit(min(max(limit,1),200))]
def get_scan(scan_id):
    if not SessionLocal:return None
    with SessionLocal() as db:
        row=db.get(ScanRecord,scan_id)
        return json.loads(row.payload_json) if row else None
