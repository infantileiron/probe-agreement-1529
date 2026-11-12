import os
DATABASE_URL=os.getenv("DATABASE_URL","mysql+pymysql://probe:probe_demo@localhost:17721/probe")
REDIS_URL=os.getenv("REDIS_URL","redis://redis:6379/0")
JWT_SECRET=os.getenv("JWT_SECRET","probe-agreement-local-demo-change-before-deployment")
SEED_DEMO=os.getenv("SEED_DEMO","true").lower()=="true"
