import logging
import os
import threading
import time
import uuid
from pathlib import Path

from .config.database import Session
from .config.settings import (
 RUN_HEARTBEAT_SECONDS,
 RUN_LEASE_SECONDS,
 RUN_QUEUED_GRACE_SECONDS,
 RUN_REAP_INTERVAL_SECONDS,
)
from .models.run import CalibrationRun
from .services import run_service
from .utils.queue import client,QUEUE

logger=logging.getLogger(__name__)
heartbeat=Path(os.getenv("WORKER_HEARTBEAT_PATH","/artifacts/worker-heartbeat"))
WORKER_ID=f"worker-{uuid.uuid4().hex[:12]}"


def touch_heartbeat():
 try:
  heartbeat.parent.mkdir(parents=True,exist_ok=True)
  heartbeat.touch()
 except OSError:
  logger.debug("Heartbeat file %s not writable",heartbeat,exc_info=True)


class LeaseHeartbeat(threading.Thread):
 """计算期间定期续租；stop_event 被设置或续租失败（租约易主）时退出。"""

 def __init__(self,db_factory,run_id,token):
  super().__init__(daemon=True,name=f"heartbeat-{run_id[:8]}")
  self.db_factory=db_factory;self.run_id=run_id;self.token=token
  self.stop_event=threading.Event()

 def run(self):
  while not self.stop_event.wait(RUN_HEARTBEAT_SECONDS):
   try:
    with self.db_factory() as db:
     if not run_service.heartbeat(db,self.run_id,self.token,RUN_LEASE_SECONDS):
      logger.warning("Lease lost for run %s; abandoning computation",self.run_id);return
   except Exception:
    logger.exception("Heartbeat error for run %s",self.run_id)

 def stop(self):self.stop_event.set()


def handle_message(run_id):
 """处理一条队列信号：领取、心跳续租、计算并凭令牌提交。"""
 with Session() as db:
  token=run_service.claim(db,run_id,WORKER_ID,RUN_LEASE_SECONDS)
 if token is None:
  logger.info("Run %s already claimed or terminal; signal ignored",run_id);return
 lease=LeaseHeartbeat(Session,run_id,token);lease.start()
 try:
  with Session() as db:
   row=db.get(CalibrationRun,run_id)
   try:
    payload=run_service.compute_result(db,row)
    ok=run_service.finalize(db,run_id,token,"completed",result=payload)
   except Exception as e:
    ok=run_service.finalize(db,run_id,token,"failed",error=str(e))
   if not ok:logger.warning("Late result from %s rejected for run %s",WORKER_ID,run_id)
 finally:
  lease.stop();lease.join(timeout=RUN_HEARTBEAT_SECONDS+1)


def reconcile_loop():
 """周期性回收过期租约、补发丢失的 queued 信号。"""
 while True:
  time.sleep(RUN_REAP_INTERVAL_SECONDS)
  try:
   with Session() as db:
    reclaimed,republished=run_service.reconcile(
     db,queued_grace_seconds=RUN_QUEUED_GRACE_SECONDS)
   if reclaimed or republished:
    logger.info("Reconcile: reclaimed=%d republished=%d",reclaimed,republished)
  except Exception:
   logger.exception("Reconcile loop error")


def main():
 logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s %(message)s")
 logger.info("Starting %s",WORKER_ID)
 threading.Thread(target=reconcile_loop,daemon=True,name="reconciler").start()
 redis=client()
 while True:
  try:
   touch_heartbeat()
   item=redis.blpop(QUEUE,timeout=2)
   if item:handle_message(item[1])
  except Exception:
   logger.exception("Worker error");time.sleep(2)


if __name__=="__main__":
 main()
