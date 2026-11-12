from pydantic import BaseModel,Field,model_validator
from ..constants.enums import UNITS
class InstrumentCreate(BaseModel):
 name:str=Field(min_length=2,max_length=180)
 x_serial:str=Field(min_length=2,max_length=80)
 y_serial:str=Field(min_length=2,max_length=80)
 unit:str
 description:str=Field(default="",max_length=2000)
 @model_validator(mode="after")
 def valid_pair(self):
  if self.unit not in UNITS:raise ValueError("单位不支持")
  if self.x_serial==self.y_serial:raise ValueError("两侧探头序列号不能相同")
  return self
