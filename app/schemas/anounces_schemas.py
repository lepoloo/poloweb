from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.anounce_multimedias_schemas import AnounceMultimediaListing
from app.schemas.likes_schemas import LikeListing

class Anounce(BaseModel):
    name: str
    entertainment_site_id: str
    description: str = Field(..., max_length=65535)
    duration: int
    end_date: datetime
    class Config:
        allow_mutation = False
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=None).isoformat() if v else None
        }

    
    

class AnounceCreate(Anounce):
   pass


class AnounceListing(Anounce):
    id: str
    refnumber: str
    nb_visite: int
    active: bool
    
    class Config:
        from_attributes = True 

class AnounceDetail(AnounceListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    anounce_multimedias: List[AnounceMultimediaListing]
    likes: List[LikeListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class AnounceUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    nb_visite: Optional[int] = Field(None, ge=0)
    duration: Optional[constr(max_length=256)] = None
    end_date: Optional[datetime] = None
    class Config:
        allow_mutation = False
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=None).isoformat() if v else None
        }
