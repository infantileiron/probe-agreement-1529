import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
class ErrorMiddleware(BaseHTTPMiddleware):
 async def dispatch(self,request,call_next):
  try:return await call_next(request)
  except Exception:
   logging.exception("Request failed")
   return JSONResponse({"detail":"服务暂时无法完成请求，请重试"},status_code=500)

async def validation_error_handler(request,exc):
 errors=[{"loc":list(error["loc"]),"msg":error["msg"],"type":error["type"]} for error in exc.errors()]
 return JSONResponse({"detail":errors},status_code=422)
