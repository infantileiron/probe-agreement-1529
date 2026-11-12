from uuid import uuid4
import jwt
from ..config.settings import JWT_SECRET
from ..models.user import User
from starlette.middleware.base import BaseHTTPMiddleware
from ..config.database import Session
from ..models.audit import Audit
class AuditMiddleware(BaseHTTPMiddleware):
 async def dispatch(self,request,call_next):
  response=await call_next(request)
  if request.method in ("POST","PATCH","DELETE"):
   try:
    with Session() as db:
     actor="anonymous"
     try:
      token=request.headers.get("Authorization","").removeprefix("Bearer ")
      claims=jwt.decode(token,JWT_SECRET,algorithms=["HS256"]);user=db.get(User,claims["sub"]);actor=user.email if user else "unknown"
     except Exception:pass
     db.add(Audit(id=str(uuid4()),actor=actor,method=request.method,path=request.url.path,status=response.status_code,detail={}));db.commit()
   except Exception:pass
  return response
