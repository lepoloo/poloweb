from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.likes_schemas import LikeListing

class Reel(BaseModel):
    link_media: str
    description: str = Field(..., max_length=65535)
    
    

class ReelCreate(Reel):
   pass


class ReelListing(Reel):
    id: str
    refnumber: str
    owner_id: str
    nb_vue: int
    active: bool
    
    class Config:
        from_attributes = True 

class ReelDetail(ReelListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    likes: List[LikeListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class ReelUpdate(BaseModel):
    link_media: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    nb_vue: Optional[int] = Field(None, ge=0)
    # active: bool = True
