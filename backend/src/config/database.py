from sqlalchemy import create_engine,inspect,text
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from .settings import DATABASE_URL
class Base(DeclarativeBase): pass
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
Session=sessionmaker(bind=engine,expire_on_commit=False)
def get_db():
 with Session() as db: yield db

# 存量库补列：仅在列缺失时执行，幂等且不触碰既有数据。
# 新库由 metadata.create_all 直接建出完整结构，不会走到这里。
# 每项为 (列名, 常规DDL, 加列后是否用 created_at 回填)。
_RUN_COLUMNS=[
 ("lease_owner","VARCHAR(64) NOT NULL DEFAULT ''",False),
 ("lease_expires_at","DATETIME NULL",False),
 ("attempts","INTEGER NOT NULL DEFAULT 0",False),
 # MySQL 支持 DATETIME 列的 CURRENT_TIMESTAMP 默认；SQLite 加列不允许非常量默认，
 # 因此方言降级为 NULL 并以 created_at 回填，模型 default/onupdate 负责后续写入。
 ("updated_at","DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",True),
]
def _patch_run_schema():
 inspector=inspect(engine)
 if "runs" not in inspector.get_table_names():return
 existing={column["name"] for column in inspector.get_columns("runs")}
 is_mysql=engine.dialect.name=="mysql"
 with engine.begin() as conn:
  for name,ddl,backfill in _RUN_COLUMNS:
   if name in existing:continue
   if backfill and not is_mysql:ddl="DATETIME NULL"
   conn.execute(text(f"ALTER TABLE runs ADD COLUMN {name} {ddl}"))
   if backfill:
    conn.execute(text(f"UPDATE runs SET {name}=created_at WHERE {name} IS NULL"))

def initialize():
 from .. import models
 Base.metadata.create_all(engine)
 _patch_run_schema()
