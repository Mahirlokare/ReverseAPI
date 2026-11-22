"""Persistent scan models."""
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,Text,Integer
from sqlalchemy.orm import Mapped,mapped_column
from apiscope.db import Base
class ScanRecord(Base):
    __tablename__="scans"
    id:Mapped[str]=mapped_column(String(36),primary_key=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
    source_type:Mapped[str]=mapped_column(String(30),default="har")
    endpoint_count:Mapped[int]=mapped_column(Integer,default=0)
    payload_json:Mapped[str]=mapped_column(Text)
