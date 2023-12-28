from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class EventMultimedia(BaseModel):
    link_media: str
    event_id: str
    
    

class EventMultimediaCreate(EventMultimedia):
   pass


class EventMultimediaListing(EventMultimedia):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class EventMultimediaDetail(EventMultimediaListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class EventMultimediaUpdate(BaseModel):
    link_media: Optional[constr(max_length=256)] = None
    event_id: Optional[constr(max_length=256)] = None
    # active: bool = True
