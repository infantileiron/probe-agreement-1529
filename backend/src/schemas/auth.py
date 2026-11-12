from pydantic import BaseModel,Field
class Login(BaseModel):
 email:str=Field(min_length=3,max_length=160)
 password:str=Field(min_length=1,max_length=200)
