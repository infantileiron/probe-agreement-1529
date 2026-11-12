from sqlalchemy import String,Text,JSON,ForeignKey,Double
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class PairedDataset(RecordMixin,Base):
 __tablename__="datasets"
 name:Mapped[str]=mapped_column(String(180),unique=True)
 x_unit:Mapped[str]=mapped_column(String(20))
 y_unit:Mapped[str]=mapped_column(String(20))
 pairs:Mapped[list]=mapped_column(JSON)
 description:Mapped[str]=mapped_column(Text,default="")
