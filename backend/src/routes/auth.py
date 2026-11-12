from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from ..config.database import get_db
from ..models.user import User
from ..schemas.auth import Login
from ..utils.security import verify_password,issue
from ..utils.auth import current
router=APIRouter(prefix="/auth")
@router.post("/login")
def login(body:Login,db=Depends(get_db)):
 user=db.scalar(select(User).where(User.email==body.email))
 if user is None or not verify_password(body.password,user.password_hash):raise HTTPException(401,"账号或密码错误")
 return {"token":issue(user),"user":{"email":user.email,"role":user.role}}
@router.get("/me")
def me(user=Depends(current)):return {"email":user.email,"role":user.role}
