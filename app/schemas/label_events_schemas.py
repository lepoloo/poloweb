from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.events_schemas import EventListing

class LabelEvent(BaseModel):
    name: str
    description: str
    
    

class LabelEventCreate(LabelEvent):
   pass


class LabelEventListing(LabelEvent):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class LabelEventDetail(LabelEventListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    events: List[EventListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class LabelEventUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    

