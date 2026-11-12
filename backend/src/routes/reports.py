from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..utils.auth import current,write_user,admin
from ..schemas.report import ReportCreate
from ..controllers import report_controller as controller,common
from ..models.report import Report
from ..models.common import serialize
router=APIRouter(prefix="/reports",tags=["reports"])
@router.get("")
def listing(db=Depends(get_db),user=Depends(current)):return controller.list_all(db)
@router.get("/{ident}")
def detail(ident:str,db=Depends(get_db),user=Depends(current)):return controller.detail(db,ident)
@router.post("",status_code=201)
def create(body:ReportCreate,db=Depends(get_db),user=Depends(admin)):return controller.create(db,body)
from fastapi.responses import Response
from ..services.report_service import export
@router.get("/{ident}/csv")
def download(ident:str,db=Depends(get_db),user=Depends(current)):
 return Response(export(common.require(db,Report,ident)),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=probe-calibration.csv"})
