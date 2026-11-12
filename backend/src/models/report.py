from sqlalchemy import String,Text,JSON,ForeignKey,Double
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class Report(RecordMixin,Base):
 __tablename__="reports"
 review_id:Mapped[str]=mapped_column(ForeignKey("reviews.id"),unique=True)
 title:Mapped[str]=mapped_column(String(180))
 snapshot:Mapped[dict]=mapped_column(JSON)
