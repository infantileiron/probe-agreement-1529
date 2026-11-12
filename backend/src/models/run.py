from datetime import datetime
from sqlalchemy import String,Text,JSON,ForeignKey,Double,DateTime,Integer
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin,now
from ..config.database import Base
class CalibrationRun(RecordMixin,Base):
 __tablename__="runs"
 study_id:Mapped[str]=mapped_column(ForeignKey("studies.id"))
 status:Mapped[str]=mapped_column(String(20),default="queued")
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str]=mapped_column(Text,default="")
 # 租约与可靠性：谁在什么期限内持有该运行，attempts 记录领取次数（含中断重投）
 lease_owner:Mapped[str]=mapped_column(String(64),default="",nullable=False)
 lease_expires_at:Mapped[datetime]=mapped_column(DateTime,nullable=True)
 attempts:Mapped[int]=mapped_column(Integer,default=0,nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime,default=now,onupdate=now,nullable=False)
