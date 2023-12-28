from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class AnounceMultimedia(BaseModel):
    link_media: str
    anounce_id: str
    
    

class AnounceMultimediaCreate(AnounceMultimedia):
   pass


class AnounceMultimediaListing(AnounceMultimedia):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class AnounceMultimediaDetail(AnounceMultimediaListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class AnounceMultimediaUpdate(BaseModel):
    link_media: Optional[constr(max_length=256)] = None
    anounce_id: Optional[constr(max_length=256)] = None
    # active: bool = True
