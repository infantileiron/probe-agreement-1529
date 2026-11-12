from uuid import uuid4
from fastapi import HTTPException
from ..models.review import BiasReview
from ..models.run import CalibrationRun

def create(db,body):
 run=db.get(CalibrationRun,body.run_id)
 if run is None or run.status!="completed":raise HTTPException(409,"仅已完成运行可提交复核")
 row=BiasReview(id=str(uuid4()),**body.model_dump(),state="submitted",reviewer="");db.add(row);db.commit();return row

def approve(db,row,user):
 if row.state!="submitted":raise HTTPException(409,"复核已处理")
 row.state="approved";row.reviewer=user.email;db.commit();return row
