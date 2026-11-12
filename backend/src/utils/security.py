import hashlib,hmac,secrets
from datetime import datetime,timedelta,timezone
import jwt
from ..config.settings import JWT_SECRET
def hash_password(value):
 salt=secrets.token_hex(16);digest=hashlib.pbkdf2_hmac("sha256",value.encode(),salt.encode(),200000).hex();return salt+":"+digest
def verify_password(value,hashed):
 salt,digest=hashed.split(":");return hmac.compare_digest(digest,hashlib.pbkdf2_hmac("sha256",value.encode(),salt.encode(),200000).hex())
def issue(user): return jwt.encode({"sub":user.id,"role":user.role,"exp":datetime.now(timezone.utc)+timedelta(hours=8)},JWT_SECRET,algorithm="HS256")
