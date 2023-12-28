from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional,List
from app.schemas.schedule_times_schemas import ScheduleTimeListing

class Program(BaseModel):
    name: str
    entertainment_site_id: str
    description: str = Field(..., max_length=65535)
    
    

class ProgramCreate(Program):
   pass


class ProgramListing(Program):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class ProgramDetail(ProgramListing):
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    schedule_times : List[ScheduleTimeListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class ProgramUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    # active: bool = True
