from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class EntertainmentSiteMultimedia(BaseModel):
    link_media: str
    entertainment_site_id: str
    
    

class EntertainmentSiteMultimediaCreate(EntertainmentSiteMultimedia):
   pass


class EntertainmentSiteMultimediaListing(EntertainmentSiteMultimedia):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class EntertainmentSiteMultimediaDetail(EntertainmentSiteMultimediaListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class EntertainmentSiteMultimediaUpdate(BaseModel):
    link_media: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    # active: bool = True
