import json,random
from sqlalchemy import select,func
from src.config.database import initialize,Session
from src.models import PairedDataset,InstrumentPair,CalibrationStudy,CalibrationRun,BiasReview,Report,User
from src.utils.security import hash_password
from src.services.run_service import compute

def make_pairs():
 rng=random.Random(20261112);rows=[]
 for i in range(240):
  band=["low","middle","high"][i//80];base=20+i/239*80
  x=base+rng.gauss(0,.2);y=1.025*base+.4+rng.gauss(0,.3)
  if i in [18,83,166,211]:y+=2.8
  rows.append({"pair_id":f"JQ-{i+1:04}","range_label":band,"x":round(x,5),"y":round(y,5)})
 return rows

def seed():
 initialize()
 with Session() as db:
  for role in ["admin","analyst","viewer"]:
   email=role+"@probe.demo"
   if not db.scalar(select(User).where(User.email==email)):db.add(User(id="user-"+role,email=email,role=role,password_hash=hash_password("ProbeDemo2026!")))
  if not db.get(PairedDataset,"demo-dataset"):db.add(PairedDataset(id="demo-dataset",name="霁川双探头 2026-11 配对",x_unit="kPa",y_unit="kPa",pairs=make_pairs(),description="240组模拟成对读数、三量程；文件jichuan_probe_pairs_202611.csv"))
  if not db.get(InstrumentPair,"demo-instrument"):db.add(InstrumentPair(id="demo-instrument",name="JQ-P17 / JQ-P18 压力探头",x_serial="JQ-P17",y_serial="JQ-P18",unit="kPa",description="两侧均有测量误差；误差方差比来自模拟重复测量假设"))
  db.commit()
  if not db.get(CalibrationStudy,"demo-study"):db.add(CalibrationStudy(id="demo-study",name="三量程压力探头比对",dataset_id="demo-dataset",instrument_id="demo-instrument",variance_ratio=2.25,tolerance=2.))
  db.commit()
  if not db.get(CalibrationRun,"demo-run"):db.add(CalibrationRun(id="demo-run",study_id="demo-study",status="queued",result={},error=""));db.commit();compute(db,"demo-run")
  if not db.get(BiasReview,"demo-review"):db.add(BiasReview(id="demo-review",run_id="demo-run",action="先复核高量程的比例偏倚与四个偏差点；一致性界限不是CI，不能据此直接判定两探头可互换。",state="approved",reviewer="admin@probe.demo"))
  db.commit()
  if not db.get(Report,"demo-report"):db.add(Report(id="demo-report",review_id="demo-review",title="霁川双探头校准复核底稿",snapshot={"result":db.get(CalibrationRun,"demo-run").result,"action":db.get(BiasReview,"demo-review").action,"reviewer":"admin@probe.demo"}))
  db.commit()
  return {cls.__tablename__:db.scalar(select(func.count()).select_from(cls)) for cls in [User,PairedDataset,InstrumentPair,CalibrationStudy,CalibrationRun,BiasReview,Report]}
if __name__=="__main__":print(json.dumps(seed(),ensure_ascii=False))
