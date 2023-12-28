from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional
from app.models.models import WeekdayEnum

class ScheduleTime(BaseModel):
    daily_day: WeekdayEnum
    open_hour: str
    close_hour: str
    program_id: str
    
    

class ScheduleTimeCreate(ScheduleTime):
   pass


class ScheduleTimeListing(ScheduleTime):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class ScheduleTimeDetail(ScheduleTimeListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class ScheduleTimeUpdate(BaseModel):
    daily_day: Optional[constr(max_length=256)] = None
    open_hour: Optional[constr(max_length=256)] = None
    close_hour: Optional[constr(max_length=256)] = None
    program_id: Optional[constr(max_length=256)] = None
    

