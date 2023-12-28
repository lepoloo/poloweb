from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.entertainment_sites_schemas import EntertainmentSiteListing

class Quarter(BaseModel):
    name: str
    town_id: str
    
    
    

class QuarterCreate(Quarter):
   pass


class QuarterListing(Quarter):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class QuarterDetail(QuarterListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    entertainment_sites : List[EntertainmentSiteListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class QuarterUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    town_id: Optional[constr(max_length=256)] = None
    
    # active: bool = True
