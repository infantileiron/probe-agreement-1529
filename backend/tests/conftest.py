import os
import sys
import pathlib
import tempfile

import fakeredis
import pytest

BACKEND=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))

_TMP=tempfile.mkdtemp(prefix="probe-test-")
os.environ["DATABASE_URL"]=f"sqlite+pysqlite:///{_TMP}/reliability.db?timeout=30"
os.environ["REDIS_URL"]="redis://ignored:6379/0"
os.environ["RUN_LEASE_SECONDS"]="30"
os.environ["RUN_HEARTBEAT_SECONDS"]="10"
os.environ["RUN_REAP_INTERVAL_SECONDS"]="5"
os.environ["RUN_QUEUED_GRACE_SECONDS"]="5"
os.environ["WORKER_HEARTBEAT_PATH"]=f"{_TMP}/worker-heartbeat"

from src.config.database import Base,Session,engine  # noqa: E402
from src.models.dataset import PairedDataset  # noqa: E402
from src.models.instrument import InstrumentPair  # noqa: E402
from src.models.study import CalibrationStudy  # noqa: E402
from src.models.run import CalibrationRun  # noqa: E402
from src.models.review import BiasReview  # noqa: E402
from src.models.report import Report  # noqa: E402
from src.utils import queue as queue_mod  # noqa: E402
from src import worker as worker_mod  # noqa: E402


def _pairs(n=6):
 return [{"pair_id":f"P{i:03d}","range_label":"low","x":float(i),"y":float(i)+0.5} for i in range(1,n+1)]


@pytest.fixture
def db():
 Base.metadata.drop_all(engine)
 Base.metadata.create_all(engine)
 with Session() as session:
  session.add(PairedDataset(id="ds-ok",name="数据集A",x_unit="kPa",y_unit="kPa",pairs=_pairs()))
  session.add(PairedDataset(id="ds-bad",name="数据集B",x_unit="kPa",y_unit="bar",pairs=_pairs()))
  session.add(InstrumentPair(id="ip-ok",name="探头组合A",x_serial="X1",y_serial="Y1",unit="kPa"))
  session.add(CalibrationStudy(id="st-ok",name="研究A",dataset_id="ds-ok",instrument_id="ip-ok",variance_ratio=1.0,tolerance=2.0))
  session.add(CalibrationStudy(id="st-bad",name="研究B",dataset_id="ds-bad",instrument_id="ip-ok",variance_ratio=1.0,tolerance=2.0))
  session.commit()
  yield session


@pytest.fixture
def fake_redis(monkeypatch):
 redis=fakeredis.FakeStrictRedis(decode_responses=True)
 monkeypatch.setattr(queue_mod,"client",lambda:redis)
 monkeypatch.setattr(worker_mod,"client",lambda:redis)
 return redis


def make_run(session,run_id="run-1",study_id="st-ok",status="queued"):
 row=CalibrationRun(id=run_id,study_id=study_id,status=status,result={},error="")
 session.add(row);session.commit()
 return row


def _detached(row):
 if row is None:return None
 Session.object_session(row).expunge(row)
 return row


def get_run(run_id):
 with Session() as s:
  return _detached(s.get(CalibrationRun,run_id))


def get_report(report_id):
 with Session() as s:
  return _detached(s.get(Report,report_id))


def get_review(review_id):
 with Session() as s:
  return _detached(s.get(BiasReview,review_id))
