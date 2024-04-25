from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
# from app.schemas.entertainment_sites_schemas import EntertainmentSiteListing
# from app.schemas.label_events_schemas import LabelEventListing
from app.schemas.event_multimedias_schemas import EventMultimediaListing
from app.schemas.likes_schemas import LikeListing

class Event(BaseModel):
    name: str
    description: str = Field(..., max_length=65535)
    label_event_id: str
    entertainment_site_id: str
    start_date: datetime
    end_date: datetime
    start_hour: str
    end_hour: str
    class Config:
        allow_mutation = False
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=None).isoformat() if v else None
        }
    
    

class EventCreate(Event):
   pass


class EventListing(Event):
    id: str
    refnumber: str
    nb_visite: int
    active: bool
    
    class Config:
        from_attributes = True 

class EventDetail(EventListing):
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    # entertainment_site: EntertainmentSiteListing
    # label_event: LabelEventListing
    event_multimedias: List[EventMultimediaListing]
    likes: List[LikeListing]
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class EventUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    label_event_id: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    nb_visite: Optional[int] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_hour: Optional[constr(max_length=256)] = None
    end_hour: Optional[constr(max_length=256)] = None
    class Config:
        allow_mutation = False
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=None).isoformat() if v else None
        }
   