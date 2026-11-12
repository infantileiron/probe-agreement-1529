from pydantic import BaseModel,Field,model_validator
from ..constants.enums import UNITS
class DatasetCreate(BaseModel):
 name:str=Field(min_length=2,max_length=180)
 x_unit:str
 y_unit:str
 csv_text:str=Field(min_length=20,max_length=2000000)
 description:str=Field(default="",max_length=2000)
 @model_validator(mode="after")
 def unit_check(self):
  if self.x_unit!=self.y_unit or self.x_unit not in UNITS:raise ValueError("两侧单位须相同，且属于支持的单位；不会自动换算")
  return self
class DatasetEdit(BaseModel):
 description:str=Field(max_length=2000)
