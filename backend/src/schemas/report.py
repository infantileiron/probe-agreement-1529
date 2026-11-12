from pydantic import BaseModel,Field
class ReportCreate(BaseModel):
 review_id:str
 title:str=Field(min_length=2,max_length=180)
