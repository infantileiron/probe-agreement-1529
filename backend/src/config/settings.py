import os
DATABASE_URL=os.getenv("DATABASE_URL","mysql+pymysql://probe:probe_demo@localhost:17721/probe")
REDIS_URL=os.getenv("REDIS_URL","redis://redis:6379/0")
JWT_SECRET=os.getenv("JWT_SECRET","probe-agreement-local-demo-change-before-deployment")
SEED_DEMO=os.getenv("SEED_DEMO","true").lower()=="true"
# 租约秒数：worker 心跳间隔约为租约的 1/3，到期未续租的运行会被回收重投
RUN_LEASE_SECONDS=float(os.getenv("RUN_LEASE_SECONDS","30"))
RUN_HEARTBEAT_SECONDS=float(os.getenv("RUN_HEARTBEAT_SECONDS","10"))
# 协调循环间隔与新入队宽限（宽限内的 queued 不重复发信号，给首次入队留出时间）
RUN_REAP_INTERVAL_SECONDS=float(os.getenv("RUN_REAP_INTERVAL_SECONDS","5"))
RUN_QUEUED_GRACE_SECONDS=float(os.getenv("RUN_QUEUED_GRACE_SECONDS","5"))
