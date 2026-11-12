import csv,io
from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.review import BiasReview
from ..models.run import CalibrationRun
from ..models.report import Report

def create(db,body):
 review=db.get(BiasReview,body.review_id)
 if review is None or review.state!="approved":raise HTTPException(409,"报告必须关联已批准的偏倚复核")
 existing=db.scalar(select(Report).where(Report.review_id==body.review_id))
 if existing:return existing
 run=db.get(CalibrationRun,review.run_id);row=Report(id=str(uuid4()),review_id=review.id,title=body.title,snapshot={"result":run.result,"action":review.action,"reviewer":review.reviewer});db.add(row);db.commit();return row

def export(row):
 out=io.StringIO();writer=csv.writer(out);writer.writerow(["pair_id","range_label","x","y","unit","mean","difference_y_minus_x","deming_fitted_y","residual_y","outside_loa","outside_tolerance"])
 for p in row.snapshot["result"]["points"]:writer.writerow([p["pair_id"],p["range_label"],p["x"],p["y"],row.snapshot["result"]["unit"],p["mean"],p["difference"],p["fitted_y"],p["residual_y"],p["outside_loa"],p["outside_tolerance"]])
 return "\ufeff"+out.getvalue()
