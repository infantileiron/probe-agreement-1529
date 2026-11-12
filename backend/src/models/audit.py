from sqlalchemy import String,JSON
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class Audit(RecordMixin,Base):
 __tablename__="audits"
 actor:Mapped[str]=mapped_column(String(160))
 method:Mapped[str]=mapped_column(String(10))
 path:Mapped[str]=mapped_column(String(300))
 status:Mapped[int]
 detail:Mapped[dict]=mapped_column(JSON,default=dict)
