from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.instrument import InstrumentPair

def create(db,body):
 if db.scalar(select(InstrumentPair).where(InstrumentPair.name==body.name)):raise HTTPException(409,"探头组合名称已存在")
 row=InstrumentPair(id=str(uuid4()),**body.model_dump());db.add(row);db.commit();return row
