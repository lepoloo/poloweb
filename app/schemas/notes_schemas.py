from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class Note(BaseModel):
    owner_id: str
    entertainment_site_id: str
    note: float = Field(..., description="Cet attribut supérieur à 0.")
    
    

class NoteCreate(Note):
   pass


class NoteListing(Note):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class NoteDetail(NoteListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class NoteUpdate(BaseModel):
    owner_id: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    note: Optional[float] = Field(None, ge=0)
    # active: bool = True
