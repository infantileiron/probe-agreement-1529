from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..utils.auth import current,write_user,admin
from ..schemas.review import ReviewCreate
from ..controllers import review_controller as controller,common
from ..models.review import BiasReview
from ..models.common import serialize
router=APIRouter(prefix="/reviews",tags=["reviews"])
@router.get("")
def listing(db=Depends(get_db),user=Depends(current)):return controller.list_all(db)
@router.get("/{ident}")
def detail(ident:str,db=Depends(get_db),user=Depends(current)):return controller.detail(db,ident)
@router.post("",status_code=201)
def create(body:ReviewCreate,db=Depends(get_db),user=Depends(write_user)):return controller.create(db,body)
from ..services.review_service import approve
@router.post("/{ident}/approve")
def approve_review(ident:str,db=Depends(get_db),user=Depends(admin)):
 return serialize(approve(db,common.require(db,BiasReview,ident),user))
