from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.menus_schemas import MenuListing

class Card(BaseModel):
    name: str
    family_card_id: str
    entertainment_site_id: str
    description: str = Field(..., max_length=65535)
    
    
    

class CardCreate(Card):
   multimedia: str


class CardListing(Card):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class CardDetail(CardListing):
    
    multimedia: str
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    menus: List[MenuListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class CardUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    family_card_id: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    multimedia: Optional[constr(max_length=256)] = None
    # active: bool = True
