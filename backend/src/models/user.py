from sqlalchemy import String
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class User(RecordMixin,Base):
 __tablename__="users"
 email:Mapped[str]=mapped_column(String(160),unique=True)
 password_hash:Mapped[str]=mapped_column(String(300))
 role:Mapped[str]=mapped_column(String(20))
