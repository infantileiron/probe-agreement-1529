from fastapi import APIRouter,Depends
from sqlalchemy import select
from ..config.database import get_db
from ..utils.auth import admin
from ..models.audit import Audit
from ..models.common import serialize
router=APIRouter()
@router.get("/audits")
def listing(db=Depends(get_db),user=Depends(admin)):return [serialize(a) for a in db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(100))]
