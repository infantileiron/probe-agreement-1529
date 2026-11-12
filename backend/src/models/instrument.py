from sqlalchemy import String,Text,JSON,ForeignKey,Double
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class InstrumentPair(RecordMixin,Base):
 __tablename__="instruments"
 name:Mapped[str]=mapped_column(String(180),unique=True)
 x_serial:Mapped[str]=mapped_column(String(80))
 y_serial:Mapped[str]=mapped_column(String(80))
 unit:Mapped[str]=mapped_column(String(20))
 description:Mapped[str]=mapped_column(Text,default="")
