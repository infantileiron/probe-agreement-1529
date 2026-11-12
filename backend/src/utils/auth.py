import jwt
from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..config.settings import JWT_SECRET
from ..models.user import User
bearer=HTTPBearer(auto_error=False)
def current(credentials=Depends(bearer),db:Session=Depends(get_db)):
 if credentials is None: raise HTTPException(401,"请先登录")
 try: claims=jwt.decode(credentials.credentials,JWT_SECRET,algorithms=["HS256"]);user=db.get(User,claims["sub"])
 except Exception: raise HTTPException(401,"登录已失效")
 if user is None: raise HTTPException(401,"账号不存在")
 return user
def write_user(user=Depends(current)):
 if user.role not in ("admin","analyst"): raise HTTPException(403,"当前账号仅可浏览")
 return user
def admin(user=Depends(current)):
 if user.role!="admin": raise HTTPException(403,"仅管理员可复核归档")
 return user
