from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..utils.auth import current,write_user,admin
from ..schemas.run import RunCreate
from ..controllers import run_controller as controller,common
from ..models.run import CalibrationRun
from ..models.common import serialize
router=APIRouter(prefix="/runs",tags=["runs"])
@router.get("")
def listing(db=Depends(get_db),user=Depends(current)):return controller.list_all(db)
@router.get("/{ident}")
def detail(ident:str,db=Depends(get_db),user=Depends(current)):return controller.detail(db,ident)
@router.post("",status_code=201)
def create(body:RunCreate,db=Depends(get_db),user=Depends(write_user)):return controller.create(db,body)
