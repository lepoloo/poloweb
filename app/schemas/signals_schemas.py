from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class Signal(BaseModel):
    owner_id: str
    event_id: Optional[constr(max_length=256)] = None
    anounce_id: Optional[constr(max_length=256)] = None
    reel_id: Optional[constr(max_length=256)] = None
    story_id: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    
    

class SignalCreate(Signal):
   pass


class SignalListing(Signal):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class SignalDetail(SignalListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class SignalUpdate(BaseModel):
    owner_id: Optional[constr(max_length=256)] = None
    event_id: Optional[constr(max_length=256)] = None
    anounce_id: Optional[constr(max_length=256)] = None
    reel_id: Optional[constr(max_length=256)] = None
    story_id: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    

