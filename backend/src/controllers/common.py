from fastapi import HTTPException
from sqlalchemy import select
from ..models.common import serialize
def listing(db,cls):
 ids=db.scalars(select(cls.id).order_by(cls.created_at.desc()).limit(200)).all()
 return [serialize(db.get(cls,ident)) for ident in ids]
def require(db,cls,ident):
 row=db.get(cls,ident)
 if row is None:raise HTTPException(404,"记录不存在")
 return row
