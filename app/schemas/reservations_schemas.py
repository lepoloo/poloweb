from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class Reservation(BaseModel):
    entertainment_site_id: str
    date: datetime
    nb_personne: PositiveInt = Field(None, gt=0)
    hour: str
    description: Optional[constr(max_length=65535)] = None
    
    

class ReservationCreate(Reservation):
   pass


class ReservationListing(Reservation):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class ReservationDetail(ReservationListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class ReservationUpdate(BaseModel):
    
    entertainment_site_id: Optional[constr(max_length=256)] = None
    hour: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    nb_personne: Optional[PositiveInt] = Field(None, gt=0)
    # active: bool = True
