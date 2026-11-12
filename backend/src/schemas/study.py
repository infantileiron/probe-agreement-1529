from pydantic import BaseModel,Field
class StudyCreate(BaseModel):
 name:str=Field(min_length=2,max_length=180)
 dataset_id:str
 instrument_id:str
 variance_ratio:float=Field(default=2.25,gt=0,le=1000000,allow_inf_nan=False)
 tolerance:float=Field(default=2,gt=0,le=1000000,allow_inf_nan=False)
