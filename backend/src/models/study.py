from sqlalchemy import String,Text,JSON,ForeignKey,Double
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class CalibrationStudy(RecordMixin,Base):
 __tablename__="studies"
 name:Mapped[str]=mapped_column(String(180),unique=True)
 dataset_id:Mapped[str]=mapped_column(ForeignKey("datasets.id"))
 instrument_id:Mapped[str]=mapped_column(ForeignKey("instruments.id"))
 variance_ratio:Mapped[float]=mapped_column(Double)
 tolerance:Mapped[float]=mapped_column(Double)
