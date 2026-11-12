from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..utils.auth import current,write_user,admin
from ..schemas.dataset import DatasetCreate
from ..controllers import dataset_controller as controller,common
from ..models.dataset import PairedDataset
from ..models.common import serialize
router=APIRouter(prefix="/datasets",tags=["datasets"])
@router.get("")
def listing(db=Depends(get_db),user=Depends(current)):return controller.list_all(db)
@router.get("/{ident}")
def detail(ident:str,db=Depends(get_db),user=Depends(current)):return controller.detail(db,ident)
@router.post("",status_code=201)
def create(body:DatasetCreate,db=Depends(get_db),user=Depends(write_user)):return controller.create(db,body)
from ..schemas.dataset import DatasetEdit
@router.patch("/{ident}")
def edit(ident:str,body:DatasetEdit,db=Depends(get_db),user=Depends(write_user)):
 row=common.require(db,PairedDataset,ident);row.description=body.description;db.commit();return serialize(row)
