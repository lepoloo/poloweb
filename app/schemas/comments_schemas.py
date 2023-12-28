from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class Comment(BaseModel):
    note: PositiveInt = Field(None, gt=0)
    content: str = Field(..., max_length=65535)
    entertainment_site_id: str
    

class CommentCreate(Comment):
   pass


class CommentListing(Comment):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class CommentDetail(CommentListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class CommentUpdate(BaseModel):
    
    entertainment_site_id: Optional[constr(max_length=256)] = None
    content: Optional[constr(max_length=65535)] = None
    note: Optional[PositiveInt] = Field(None, gt=0)
    # active: bool = True
