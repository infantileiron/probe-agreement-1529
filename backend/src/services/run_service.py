import logging
from datetime import timedelta
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select,update
from ..config.settings import RUN_LEASE_SECONDS
from ..models.common import now
from ..models.run import CalibrationRun
from ..models.study import CalibrationStudy
from ..models.dataset import PairedDataset
from ..models.instrument import InstrumentPair
from ..utils.queue import enqueue,queued_ids
from .paired_data import validate_pairs
from .deming import regress
from .agreement import analyze

logger=logging.getLogger(__name__)

def create(db,body):
 if not db.get(CalibrationStudy,body.study_id):raise HTTPException(422,"校准研究不存在")
 row=CalibrationRun(id=str(uuid4()),study_id=body.study_id,status="queued",result={},error="");db.add(row);db.commit()
 try:enqueue(row.id)
 except Exception:
  # Redis 不可用时行仍保留为 queued，协调循环会在 Redis 恢复后自动补发
  logger.exception("Enqueue signal failed for run %s; reconciler will republish",row.id)
 return row

def claim(db,run_id,owner,lease_seconds=RUN_LEASE_SECONDS):
 """原子领取：仅 queued 或租约已过期的 running 可被领取，成功返回新的租约令牌。

 同一运行被同时领取或重复投递时，数据库行级 UPDATE 保证只有一个领取者胜出；
 后到者拿到 None，不会产生第二份计算。owner 仅用于日志排查，令牌本身作为凭证。
 """
 moment=now();deadline=moment+timedelta(seconds=float(lease_seconds));token=str(uuid4())
 result=db.execute(
  update(CalibrationRun)
  .where(CalibrationRun.id==run_id)
  .where((CalibrationRun.status=="queued")
         |((CalibrationRun.status=="running")
           &(CalibrationRun.lease_expires_at.is_not(None))
           &(CalibrationRun.lease_expires_at<moment)))
  .values(status="running",lease_owner=token,lease_expires_at=deadline,
          attempts=CalibrationRun.attempts+1,updated_at=moment)
 )
 db.commit()
 if result.rowcount!=1:return None
 logger.info("Run %s claimed by %s (token %s)",run_id,owner,token[:8])
 return token

def heartbeat(db,run_id,token,lease_seconds=RUN_LEASE_SECONDS):
 """持有有效令牌才续租；租约已被他人接管时返回 False，调用方应停止计算。"""
 result=db.execute(
  update(CalibrationRun)
  .where(CalibrationRun.id==run_id,CalibrationRun.lease_owner==token,CalibrationRun.status=="running")
  .values(lease_expires_at=now()+timedelta(seconds=float(lease_seconds)),updated_at=now())
 )
 db.commit()
 return result.rowcount==1

def finalize(db,run_id,token,status,result=None,error=""):
 """凭租约令牌写终态。过期领取者（令牌已不匹配）的晚到结果无法覆盖新结果。"""
 if status not in ("completed","failed"):raise ValueError("终态只能是 completed 或 failed")
 values={"status":status,"error":error[:1000],"lease_owner":"","lease_expires_at":None,"updated_at":now()}
 if result is not None:values["result"]=result
 affected=db.execute(
  update(CalibrationRun)
  .where(CalibrationRun.id==run_id,CalibrationRun.lease_owner==token,CalibrationRun.status=="running")
  .values(**values)
 )
 db.commit()
 return affected.rowcount==1

def compute_result(db,row):
 """纯计算：读取研究/数据集/探头并产出结果载荷，失败抛异常。"""
 study=db.get(CalibrationStudy,row.study_id);dataset=db.get(PairedDataset,study.dataset_id);pair=db.get(InstrumentPair,study.instrument_id)
 if dataset.x_unit!=dataset.y_unit or dataset.x_unit!=pair.unit:raise ValueError("单位不一致")
 x,y=validate_pairs(dataset.pairs);deming=regress(x,y,study.variance_ratio);ba=analyze(x,y)
 points=[{**p,"fitted_y":deming["intercept"]+deming["slope"]*p["x"],"residual_y":p["y"]-deming["intercept"]-deming["slope"]*p["x"],"mean":(p["x"]+p["y"])/2,"difference":p["y"]-p["x"],"outside_loa":p["y"]-p["x"]<ba["loa_low"] or p["y"]-p["x"]>ba["loa_high"],"outside_tolerance":abs(p["y"]-p["x"])>study.tolerance} for p in dataset.pairs]
 return {"dataset_name":dataset.name,"instrument_name":pair.name,"x_serial":pair.x_serial,"y_serial":pair.y_serial,"unit":pair.unit,"n":len(points),"deming":deming,"agreement":ba,"points":points,"tolerance":study.tolerance,"outside_tolerance":sum(p["outside_tolerance"] for p in points)}

def process(db,run_id,owner,lease_seconds=RUN_LEASE_SECONDS):
 """worker 入口：领取 -> 计算 -> 凭令牌提交。返回是否由本调用完成终态写入。"""
 token=claim(db,run_id,owner,lease_seconds)
 if token is None:return False
 row=db.get(CalibrationRun,run_id)
 try:
  payload=compute_result(db,row)
  ok=finalize(db,run_id,token,"completed",result=payload)
 except Exception as e:
  ok=finalize(db,run_id,token,"failed",error=str(e))
  if not ok:logger.warning("Stale worker failure rejected for run %s",run_id)
  return ok
 if not ok:logger.warning("Stale worker result rejected for run %s",run_id)
 return ok

def reconcile(db,queued_grace_seconds=5.0):
 """恢复异常中断与消息丢失，返回 (回收数, 补发数)。

 1. running 且租约过期（worker 崩溃/卡死）：退回 queued 并重新发信号；
 2. queued 且超过入队宽限但 Redis 信号队列中没有对应消息（消息丢失）：补发信号。
 终态 completed/failed 一律不动，已完成底稿和批准报告保持原样。
 """
 reclaimed=republished=0
 moment=now()
 stale=db.scalars(select(CalibrationRun).where(
  CalibrationRun.status=="running",
  CalibrationRun.lease_expires_at.is_not(None),
  CalibrationRun.lease_expires_at<moment)).all()
 reclaimed_ids=[]
 for row in stale:
  row.status="queued";row.lease_owner="";row.lease_expires_at=None;row.updated_at=moment
  reclaimed_ids.append(row.id)
 if stale:db.commit()
 for ident in reclaimed_ids:
  try:enqueue(ident);reclaimed+=1
  except Exception:logger.exception("Re-enqueue failed for reclaimed run %s; next reconcile retries",ident)
 try:signals=queued_ids()
 except Exception:
  logger.exception("Redis unavailable during reconcile; queued republish deferred")
  return reclaimed,republished
 cutoff=moment-timedelta(seconds=float(queued_grace_seconds))
 waiting=db.scalars(select(CalibrationRun).where(
  CalibrationRun.status=="queued",CalibrationRun.updated_at<cutoff)).all()
 for row in waiting:
  if row.id not in signals:
   try:enqueue(row.id);republished+=1
   except Exception:logger.exception("Republish failed for queued run %s",row.id)
 return reclaimed,republished

def compute(db,run_id):
 """同步计算入口（种子/本地脚本使用）：自领租约并立即提交，同样受令牌保护。

 与历史行为一致：计算失败落在运行的 failed 状态上，不向调用方抛异常。
 """
 token=claim(db,run_id,f"sync-{uuid4()}",lease_seconds=max(RUN_LEASE_SECONDS,60.0))
 if token is None:return
 row=db.get(CalibrationRun,run_id)
 try:
  payload=compute_result(db,row);finalize(db,run_id,token,"completed",result=payload)
 except Exception as e:
  logger.exception("Synchronous compute failed for run %s",run_id)
  finalize(db,run_id,token,"failed",error=str(e))
