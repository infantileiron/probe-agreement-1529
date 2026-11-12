from uuid import uuid4
from fastapi import HTTPException
from ..models.run import CalibrationRun
from ..models.study import CalibrationStudy
from ..models.dataset import PairedDataset
from ..models.instrument import InstrumentPair
from ..utils.queue import enqueue
from .paired_data import validate_pairs
from .deming import regress
from .agreement import analyze

def create(db,body):
 if not db.get(CalibrationStudy,body.study_id):raise HTTPException(422,"校准研究不存在")
 row=CalibrationRun(id=str(uuid4()),study_id=body.study_id,status="queued",result={},error="");db.add(row);db.commit()
 try:enqueue(row.id)
 except Exception:
  row.status="failed";row.error="Redis队列不可用，请稍后重试";db.commit();raise HTTPException(503,row.error)
 return row

def compute(db,run_id):
 row=db.get(CalibrationRun,run_id)
 if row is None or row.status not in ["queued","running"]:return
 row.status="running";db.commit()
 try:
  study=db.get(CalibrationStudy,row.study_id);dataset=db.get(PairedDataset,study.dataset_id);pair=db.get(InstrumentPair,study.instrument_id)
  if dataset.x_unit!=dataset.y_unit or dataset.x_unit!=pair.unit:raise ValueError("单位不一致")
  x,y=validate_pairs(dataset.pairs);deming=regress(x,y,study.variance_ratio);ba=analyze(x,y)
  points=[{**p,"fitted_y":deming["intercept"]+deming["slope"]*p["x"],"residual_y":p["y"]-deming["intercept"]-deming["slope"]*p["x"],"mean":(p["x"]+p["y"])/2,"difference":p["y"]-p["x"],"outside_loa":p["y"]-p["x"]<ba["loa_low"] or p["y"]-p["x"]>ba["loa_high"],"outside_tolerance":abs(p["y"]-p["x"])>study.tolerance} for p in dataset.pairs]
  row.result={"dataset_name":dataset.name,"instrument_name":pair.name,"x_serial":pair.x_serial,"y_serial":pair.y_serial,"unit":pair.unit,"n":len(points),"deming":deming,"agreement":ba,"points":points,"tolerance":study.tolerance,"outside_tolerance":sum(p["outside_tolerance"] for p in points)};row.status="completed"
 except Exception as e:row.status="failed";row.error=str(e)[:1000]
 db.commit()
