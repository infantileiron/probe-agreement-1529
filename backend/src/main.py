import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from .config.database import initialize,Session
from .config.settings import SEED_DEMO
from .utils.queue import client
from .middlewares.audit import AuditMiddleware
from .middlewares.errors import ErrorMiddleware,validation_error_handler
from .routes import auth,datasets,instruments,studies,runs,reviews,reports,audit
@asynccontextmanager
async def lifespan(app):
 initialize()
 if SEED_DEMO:
  try:
   from scripts.seed_demo import seed
   seed()
  except Exception:logging.exception("Demo seed failed; app remains available")
 yield
app=FastAPI(title="霁川观测 · 双探头读数校准",lifespan=lifespan)
app.add_exception_handler(RequestValidationError,validation_error_handler)
app.add_middleware(AuditMiddleware);app.add_middleware(ErrorMiddleware)
for module in [auth,datasets,instruments,studies,runs,reviews,reports,audit]:app.include_router(module.router)
@app.get("/health")
def health():
 with Session() as db:db.execute(text("SELECT 1"))
 client().ping();return {"status":"ok"}
