import threading
import time
from datetime import timedelta

from conftest import make_run,get_run,get_report,get_review
from src.config.database import Session
from src.models.common import now
from src.models.run import CalibrationRun
from src.models.review import BiasReview
from src.models.report import Report
from src.services import run_service
from src import worker as worker_mod


# ---------- 领取原子性：重复投递 / 并发只保留一份有效处理 ----------

def test_duplicate_delivery_only_first_claim_wins(db,fake_redis):
 make_run(db,"run-dup")
 fake_redis.rpush("probe-agreement:runs","run-dup")
 fake_redis.rpush("probe-agreement:runs","run-dup")  # 重复投递
 with Session() as s:
  token1=run_service.claim(s,"run-dup","worker-a")
  token2=run_service.claim(s,"run-dup","worker-b")
 assert token1 is not None and token2 is None
 row=get_run("run-dup")
 assert row.status=="running" and row.attempts==1 and row.lease_owner==token1


def test_concurrent_claims_have_single_winner(db,fake_redis):
 make_run(db,"run-race")
 winners=[];lock=threading.Lock()
 def grab(owner):
  with Session() as s:
   token=run_service.claim(s,"run-race",owner)
   if token:
    with lock:winners.append(token)
 threads=[threading.Thread(target=grab,args=(f"w{i}",)) for i in range(8)]
 for t in threads:t.start()
 for t in threads:t.join()
 assert len(winners)==1
 row=get_run("run-race")
 assert row.attempts==1 and row.status=="running"


def test_duplicate_signal_does_not_produce_double_result(db,fake_redis):
 make_run(db,"run-sig")
 fake_redis.rpush("probe-agreement:runs","run-sig")
 fake_redis.rpush("probe-agreement:runs","run-sig")  # 重复信号
 worker_mod.handle_message("run-sig")
 worker_mod.handle_message("run-sig")
 row=get_run("run-sig")
 assert row.status=="completed" and row.attempts==1
 assert row.result and row.lease_owner=="" and row.lease_expires_at is None


# ---------- 正常完成与失败 ----------

def test_process_completes_and_clears_lease(db,fake_redis):
 make_run(db,"run-ok")
 with Session() as s:
  assert run_service.process(s,"run-ok","worker-a") is True
 row=get_run("run-ok")
 assert row.status=="completed" and row.result["n"]==6
 assert row.lease_owner=="" and row.lease_expires_at is None and row.attempts==1


def test_process_failure_marks_failed(db,fake_redis):
 make_run(db,"run-fail",study_id="st-bad")
 with Session() as s:
  assert run_service.process(s,"run-fail","worker-a") is True
 row=get_run("run-fail")
 assert row.status=="failed" and "单位不一致" in row.error
 assert row.lease_owner=="" and row.lease_expires_at is None


# ---------- 异常中断：租约过期后回收、重投、重新计算 ----------

def test_crashed_worker_run_is_reclaimed_and_completed(db,fake_redis):
 make_run(db,"run-crash")
 with Session() as s:
  token_a=run_service.claim(s,"run-crash","worker-a",lease_seconds=0.05)
 assert token_a is not None
 time.sleep(0.1)  # worker-a 崩溃，租约过期，底稿停在 running
 assert get_run("run-crash").status=="running"
 with Session() as s:
  reclaimed,republished=run_service.reconcile(s,queued_grace_seconds=0)
 assert (reclaimed,republished)==(1,0)
 row=get_run("run-crash")
 assert row.status=="queued" and row.lease_owner=="" and row.lease_expires_at is None
 assert fake_redis.lrange("probe-agreement:runs",0,-1)==["run-crash"]
 worker_mod.handle_message("run-crash")  # 新 worker 凭信号重新领取并完成
 row=get_run("run-crash")
 assert row.status=="completed" and row.attempts==2 and row.result["n"]==6


# ---------- 消息丢失：queued 行在信号队列消失后可找回 ----------

def test_lost_queue_message_is_republished(db,fake_redis):
 row=make_run(db,"run-lost")
 row.updated_at=now()-timedelta(seconds=30);db.commit()  # 超过宽限期仍未被领取
 assert fake_redis.llen("probe-agreement:runs")==0
 with Session() as s:
  reclaimed,republished=run_service.reconcile(s,queued_grace_seconds=5)
 assert (reclaimed,republished)==(0,1)
 assert fake_redis.lrange("probe-agreement:runs",0,-1)==["run-lost"]
 worker_mod.handle_message("run-lost")
 assert get_run("run-lost").status=="completed"


def test_fresh_queued_within_grace_is_not_duplicated(db,fake_redis):
 make_run(db,"run-fresh")  # Redis 信号正常存在
 fake_redis.rpush("probe-agreement:runs","run-fresh")
 with Session() as s:
  assert run_service.reconcile(s,queued_grace_seconds=5)==(0,0)
 assert fake_redis.llen("probe-agreement:runs")==1


def test_create_survives_redis_outage_and_republishes_later(db,monkeypatch,fake_redis):
 from src.services import run_service as rs
 from src.schemas.run import RunCreate
 original_enqueue=rs.enqueue
 def boom(_):raise RuntimeError("redis down")
 monkeypatch.setattr(rs,"enqueue",boom)
 with Session() as s:
  row=rs.create(s,RunCreate(study_id="st-ok"))
 assert row.status=="queued"
 monkeypatch.setattr(rs,"enqueue",original_enqueue)  # 仅恢复该补丁，保留 fake_redis 补丁
 run_id=row.id
 with Session() as s:
  s.get(CalibrationRun,run_id).updated_at=now()-timedelta(seconds=30);s.commit()
 with Session() as s:
  assert run_service.reconcile(s,queued_grace_seconds=5)==(0,1)
 worker_mod.handle_message(run_id)
 assert get_run(run_id).status=="completed"


# ---------- 过期领取者晚到的结果不能覆盖新结果（fencing token） ----------

def test_late_result_from_stale_owner_is_rejected(db,fake_redis):
 make_run(db,"run-fence")
 with Session() as s:
  token_a=run_service.claim(s,"run-fence","worker-a",lease_seconds=0.05)
 time.sleep(0.1)
 with Session() as s:
  token_b=run_service.claim(s,"run-fence","worker-b")
 assert token_b and token_b!=token_a
 # worker-a 晚回来，分别尝试提交成功结果与失败结果
 with Session() as s:
  assert run_service.finalize(s,"run-fence",token_a,"completed",result={"marker":"A"}) is False
  assert run_service.finalize(s,"run-fence",token_a,"failed",error="late failure") is False
 row=get_run("run-fence")
 assert row.status=="running" and row.result=={} and row.error==""
 with Session() as s:
  assert run_service.finalize(s,"run-fence",token_b,"completed",result={"marker":"B"}) is True
 row=get_run("run-fence")
 assert row.status=="completed" and row.result=={"marker":"B"}


def test_heartbeat_fails_after_lease_changes_owner(db,fake_redis):
 make_run(db,"run-hb")
 with Session() as s:
  token_a=run_service.claim(s,"run-hb","worker-a",lease_seconds=0.05)
 time.sleep(0.1)
 with Session() as s:
  assert run_service.claim(s,"run-hb","worker-b") is not None
 with Session() as s:
  assert run_service.heartbeat(s,"run-hb",token_a) is False  # 旧领取者续租被拒


# ---------- 终态稳定：completed/failed 不被协调动作改动，底稿与报告可读 ----------

def test_terminal_runs_are_never_touched(db,fake_redis):
 done=make_run(db,"run-done",status="completed");done.result={"marker":"keep"};done.error=""
 fail=make_run(db,"run-failed",status="failed",study_id="st-bad");fail.error="原始失败原因"
 db.commit()
 with Session() as s:
  assert run_service.reconcile(s,queued_grace_seconds=0)==(0,0)
 with Session() as s:
  assert run_service.claim(s,"run-done","x") is None
  assert run_service.claim(s,"run-failed","x") is None
 assert get_run("run-done").result=={"marker":"keep"}
 assert get_run("run-failed").error=="原始失败原因"


def test_completed_draft_review_and_report_remain_readable(db,fake_redis):
 run=make_run(db,"run-report",status="completed")
 run.result={"n":6,"points":[],"unit":"kPa","marker":"snapshot"}
 review=BiasReview(id="rev-1",run_id=run.id,action="同意",state="approved",reviewer="admin@probe.demo")
 report=Report(id="rep-1",review_id="rev-1",title="批准报告",snapshot={"result":run.result,"reviewer":"admin@probe.demo"})
 db.add_all([review,report]);db.commit()
 with Session() as s:
  run_service.reconcile(s,queued_grace_seconds=0)
 rerun=get_run("run-report")
 rereport=get_report("rep-1")
 assert rerun.status=="completed" and rerun.result["marker"]=="snapshot"
 assert rereport.snapshot["result"]["marker"]=="snapshot"
 assert get_review("rev-1").state=="approved"


def test_sync_compute_is_idempotent_on_terminal_run(db,fake_redis):
 make_run(db,"run-sync")
 with Session() as s:
  run_service.compute(s,"run-sync")
 assert get_run("run-sync").status=="completed"
 first=get_run("run-sync").result
 with Session() as s:
  run_service.compute(s,"run-sync")  # 已完成，不重算、不覆盖
 assert get_run("run-sync").result==first


# ---------- 端到端：真实 worker 线程 + 协调循环自动恢复崩溃任务 ----------

def test_worker_end_to_end_recovers_crashed_run(db,monkeypatch,fake_redis):
 monkeypatch.setattr(worker_mod,"RUN_REAP_INTERVAL_SECONDS",0.2)
 monkeypatch.setattr(worker_mod,"RUN_QUEUED_GRACE_SECONDS",0.0)
 thread=threading.Thread(target=worker_mod.main,daemon=True);thread.start()
 make_run(db,"run-e2e")
 fake_redis.rpush("probe-agreement:runs","run-e2e")
 deadline=time.time()+15
 while time.time()<deadline and get_run("run-e2e").status!="completed":
  time.sleep(0.1)
 assert get_run("run-e2e").status=="completed"
 # 模拟第二个任务在计算中崩溃：停留 running、租约过期、队列无信号
 crashed=make_run(db,"run-e2e-crash")
 crashed.status="running";crashed.lease_owner="dead-worker"
 crashed.lease_expires_at=now()-timedelta(seconds=30)
 crashed.updated_at=now()-timedelta(seconds=30);db.commit()
 deadline=time.time()+15
 while time.time()<deadline and get_run("run-e2e-crash").status!="completed":
  time.sleep(0.1)
 row=get_run("run-e2e-crash")
 assert row.status=="completed" and row.attempts>=1 and row.result["n"]==6
