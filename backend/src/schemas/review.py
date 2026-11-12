from pydantic import BaseModel,Field
class ReviewCreate(BaseModel):
 run_id:str
 action:str=Field(min_length=8,max_length=3000)
