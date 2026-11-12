from datetime import datetime,timezone
from sqlalchemy import String,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
def now(): return datetime.now(timezone.utc).replace(tzinfo=None)
class RecordMixin:
 id:Mapped[str]=mapped_column(String(36),primary_key=True)
 created_at:Mapped[datetime]=mapped_column(DateTime,default=now)
def serialize(row):
 return {c.name:(getattr(row,c.name).isoformat()+"Z" if isinstance(getattr(row,c.name),datetime) else getattr(row,c.name)) for c in row.__table__.columns}
