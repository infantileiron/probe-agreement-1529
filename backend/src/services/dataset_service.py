from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.dataset import PairedDataset
from .paired_data import parse_csv

def create(db,body):
 if db.scalar(select(PairedDataset).where(PairedDataset.name==body.name)):raise HTTPException(409,"配对批次名称已存在")
 try:pairs=parse_csv(body.csv_text)
 except ValueError as e:raise HTTPException(422,str(e))
 row=PairedDataset(id=str(uuid4()),name=body.name,x_unit=body.x_unit,y_unit=body.y_unit,pairs=pairs,description=body.description);db.add(row);db.commit();return row
